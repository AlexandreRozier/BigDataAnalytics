# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example implementation of code to run on the AWS SageMaker service
"""

import traceback
import argparse
import json
import os
import model
import tensorflow as tf
from model import model_fn

tf.logging.set_verbosity(tf.logging.DEBUG)


SEQ_LEN = None
N_OUTPUTS = 1  # in each sequence, 1-49 are features, and 50 is label
DEFAULTS = None
TIMESERIES_COL = 'height'
N_INPUTS = None

def init(hparams):
    global SEQ_LEN, DEFAULTS, N_INPUTS
    SEQ_LEN = hparams['sequence_length']
    DEFAULTS = [[0.0] for x in range(0, SEQ_LEN)]
    N_INPUTS = SEQ_LEN - N_OUTPUTS

def serving_input_fn():
    feature_placeholders = {
        TIMESERIES_COL: tf.placeholder(tf.float32, [None, N_INPUTS])
    }

    features = {
        key: tf.expand_dims(tensor, -1)
        for key, tensor in feature_placeholders.items()
    }
    features[TIMESERIES_COL] = tf.squeeze(features[TIMESERIES_COL], axis=[2])

    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)


# read data and convert to needed format
# dirname: s3://bucket-name/data/
def read_dataset(dirname, mode, batch_size=512):
    tf.logging.log(tf.logging.DEBUG,dirname)
    def _input_fn():
        def decode_csv(row):
            # row is a string tensor containing the contents of one row
            features = tf.decode_csv(row, record_defaults=DEFAULTS)  # string tensor -> list of 50 rank 0 float tensors
            label = features.pop()  # remove last feature and use as label
            features = tf.stack(features)  # list of rank 0 tensors -> single rank 1 tensor
        
            return {TIMESERIES_COL: features}, label

        if mode == tf.estimator.ModeKeys.TRAIN:
            dataset = tf.data.TextLineDataset(os.path.join(dirname, "train.csv"))
        elif mode == tf.estimator.ModeKeys.EVAL:
            dataset = tf.data.TextLineDataset(os.path.join(dirname, "test.csv"))

        """ # Create list of file names that match "glob" pattern (i.e. data_file_*.csv)
        dataset = tf.data.Dataset.list_files(filename)
        # Read in data from files
        dataset = dataset.flat_map(tf.data.TextLineDataset)
        """

        # Parse text lines as comma-separated values (CSV)
        dataset = dataset.map(decode_csv)
        if mode == tf.estimator.ModeKeys.TRAIN:
            num_epochs = None  # loop indefinitely
            dataset = dataset.shuffle(buffer_size=10 * batch_size)
        else:
            num_epochs = 1  # end-of-input after this

        dataset = dataset.repeat(num_epochs).batch(batch_size)
        return dataset.make_one_shot_iterator().get_next()

    return _input_fn

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    ## hyperparameters sent by the client are passed as command-line arguments to the script.
    
    # input data and model directories
    parser.add_argument(
        '--data_dir_path',
        help='S3 path to training data',
        default=os.environ.get('SM_CHANNEL_DEFAULT')
    )
  
    parser.add_argument(
        '--model_dir',
        help='?',
    )
    
    # Hyperparameters
    parser.add_argument(
        '--train_batch_size',
        help='Batch size for training steps',
        type=int,
        default=100
    )
    
    parser.add_argument(
        '--eval_batch_size',
        help='Batch size for evaluation steps',
        type=int,
        default=100
    )
    parser.add_argument(
        '--learning_rate',
        help='Initial learning rate for training',
        type=float,
        default=0.01
    )
    parser.add_argument(
        '--train_steps',
        help="""\
        Steps to run the training job for. A step is one batch-size,\
        """,
        type=int,
        default=0
    )
    parser.add_argument(
        '--eval_steps',
        help="""\
        Steps to run the eval job for. A step is one batch-size,\
        """,
        type=int,
        default=0
    )
    parser.add_argument(
        '--sequence_length',
        help="""\
        This model works with fixed length sequences. 1-(N-1) are inputs, last is output
        """,
        type=int,
        default=10
    )
    
    model_names = [name.replace('_model','') \
                    for name in dir(model) \
                    if name.endswith('_model')]
    parser.add_argument(
        '--model',
        help='Type of model. Supported types are {}'.format(model_names),
        default='linear'
    )
  
    parser.add_argument(
        '--eval_delay_secs',
        help='How long to wait before running first evaluation',
        default=10,
        type=int
    )
    parser.add_argument(
        '--min_eval_frequency',
        help='Minimum number of training steps between evaluations',
        default=60,
        type=int
    )

    args = parser.parse_args()
    hparams = args.__dict__

    

    # Starts proper training
    init(hparams)

    get_train = read_dataset(hparams['data_dir_path'],
                             tf.estimator.ModeKeys.TRAIN,
                             hparams['train_batch_size'])
    get_valid = read_dataset(hparams['data_dir_path'],
                             tf.estimator.ModeKeys.EVAL,
                             hparams['eval_batch_size'])
    estimator = tf.estimator.Estimator(model_fn=model_fn,
                                       params=hparams,
                                       config=tf.estimator.RunConfig(
                                           save_checkpoints_secs=
                                           hparams['min_eval_frequency']),
                                       model_dir=hparams['model_dir'])
    

    
    train_spec = tf.estimator.TrainSpec(input_fn=get_train,
                                        max_steps=hparams['train_steps'])
    exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)
    eval_spec = tf.estimator.EvalSpec(input_fn=get_valid,
                                      steps=None,
                                      exporters=exporter,
                                      start_delay_secs=hparams['eval_delay_secs'],
                                      throttle_secs=hparams['min_eval_frequency'])
    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
    
 
    
    #output_dir = hparams.pop('output_dir')

    # Append trial_id to path if we are doing hptuning
    # This code can be removed if you are not using hyperparameter tuning
    #output_dir = os.path.join(
    #    output_dir,
    #    json.loads(
    #        os.environ.get('TF_CONFIG', '{}')
    #    ).get('task', {}).get('trial', '')
    #)
    