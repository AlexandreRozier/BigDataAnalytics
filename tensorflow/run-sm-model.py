from sagemaker.tensorflow import TensorFlow
import sagemaker
hparams = {
    # train_data_path:  useless because populated by SageMaker
    # eval_data_path:  useless because populated by SageMaker
    #"model_dir":"output/", # if left undefined, SM will write it to the training job's bucket
    "train_batch_size":100,
    "eval_batch_size":100,
    "learning_rate":0.01,
    "train_steps":10,
    "eval_steps":10,
    "sequence_length":50,
    "model":"linear",
    "eval_delay_secs":10,
    "min_eval_frequency":10
}
sagemaker_session = sagemaker.Session()

estimator = TensorFlow(entry_point='tf-train.py',
                                  dependencies=['model.py'],
                                  role='arn:aws:iam::746022503515:role/sage_maker',
                                  framework_version='1.11.0',
                                  train_instance_count=1,
                                  hyperparameters=hparams,
                                  train_instance_type='local',
                                  py_version='py3')


estimator.fit({'default':'s3://fog-datasets/time-series-test'})
predictor = estimator.deploy(initial_instance_count=1, instance_type='ml.t2.medium')

# Do a prediction
prediction_set = tf.contrib.learn.datasets.base.load_csv_without_header(
    filename=os.path.join('dataset/test.csv'), target_dtype=np.float, features_dtype=np.float32)

data = prediction_set.data[0]
tensor_proto = tf.make_tensor_proto(values=np.asarray(data), shape=[1, len(data)], dtype=tf.float32)
abalone_predictor.predict(tensor_proto)
sagemaker.Session().delete_endpoint(abalone_predictor.endpoint)