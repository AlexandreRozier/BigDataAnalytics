import pickle
import pandas as pd
from matplotlib import pyplot as plt
from sagemaker.amazon.amazon_estimator import get_image_uri
import sagemaker
import boto3 
import s3fs
import json 

with open("data.p", 'r+b') as outfile:
    data = pickle.load(outfile)

for key, val in data.items():
    print("Key:"+key)
    if(key == 'response-code-4xx'):
        pts = val['Datapoints']



bucket = 'fog-datasets-west'
prefix = 'rcf'

sagemaker_session = sagemaker.Session()

s3_data_path = "{}/{}/data".format(bucket, prefix)
s3_output_path = "{}/{}/output".format(bucket, prefix)
image_name = get_image_uri('us-west-1', 'forecasting-deepar')
role = 'arn:aws:iam::746022503515:role/sage_maker'


freq = '10min'
df = pd.DataFrame(pts)
df.index = pd.to_datetime(df.Timestamp)
df.index = [i.replace(tzinfo=None) for i in  df.index]
df = df.drop(columns=['Timestamp','Unit'])
df = df.groupby([pd.Grouper(freq=freq)]).count()
print(df.head())

serie = pd.Series(data=df.SampleCount, index=df.index)

print(len(serie.index))

PREDICTION_LENGTH = 15
CONTEXT_LENGTH = 30

time_series = []
time_series.append(serie)

time_series_training = []
for ts in time_series:
    time_series_training.append(ts[:-PREDICTION_LENGTH])


time_series[0].plot(label='test')
time_series_training[0].plot(label='train', ls=':')
plt.legend()
#plt.show()


def series_to_obj(ts, cat=None):
    obj = {"start": str(ts.index[0]), "target": list(ts)}
    if cat is not None:
        obj["cat"] = cat
    return obj

def series_to_jsonline(ts, cat=None):
    return json.dumps(series_to_obj(ts, cat))


encoding = "utf-8"
s3filesystem = s3fs.S3FileSystem()

with s3filesystem.open(s3_data_path + "/train/train.json", 'wb') as fp:
    for ts in time_series_training:
        fp.write(series_to_jsonline(ts).encode(encoding))
        fp.write('\n'.encode(encoding))

with s3filesystem.open(s3_data_path + "/test/test.json", 'wb') as fp:
    for ts in time_series:
        fp.write(series_to_jsonline(ts).encode(encoding))
        fp.write('\n'.encode(encoding))

estimator = sagemaker.estimator.Estimator(
    sagemaker_session=sagemaker_session,
    image_name=image_name,
    role=role,
    train_instance_count=1,
    train_instance_type='ml.c4.xlarge',
    base_job_name='DEMO-deepar',
    output_path="s3://" + s3_output_path
)

hyperparameters = {
    "time_freq": freq,
    "context_length": str(CONTEXT_LENGTH),
    "prediction_length": str(PREDICTION_LENGTH),
    "num_cells": "40",
    "num_layers": "3",
    "likelihood": "gaussian",
    "epochs": "20",
    "mini_batch_size": "32",
    "learning_rate": "0.001",
    "dropout_rate": "0.05",
    "early_stopping_patience": "10"
}

estimator.set_hyperparameters(**hyperparameters)


data_channels = {
    "train": "s3://{}/train/".format(s3_data_path),
    "test": "s3://{}/test/".format(s3_data_path)
}

estimator.fit(inputs=data_channels)
