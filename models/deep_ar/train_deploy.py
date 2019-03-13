import pickle
import pandas as pd
from matplotlib import pyplot as plt
import sagemaker
import boto3 
import s3fs
import json
import datetime
from tzlocal import get_localzone as tzlocal
import numpy as np
import os
from sagemaker.amazon.amazon_estimator import get_image_uri
import boto3 
from deep_ar import DeepARPredictor

# ARN of the role used during training. This role needs access in particular to S3, since it's where our data resides.
role_arn = os.environ['SAGEMAKER_ROLE_ARN'] #'arn:aws:iam::746022503515:role/sage_maker'
data_bucket_name = os.environ['SANITIZED_DATA_BUCKET'] #'fog-datasets'
data_freq = os.environ['DATA_FREQUENCY'] #5min

image_name = get_image_uri(boto3.Session().region_name, 'forecasting-deepar')
prefix = 'deep_ar'
s3_data_path = "{}/{}/data".format(data_bucket_name, prefix)
s3_output_path = "{}/{}/output".format(data_bucket_name, prefix)

train_locally = False
train_instance_type = 'ml.m5.2xlarge'

sagemaker_session = sagemaker.Session()

# Create a Sagemaker estimator. It is an abstraction used by sagemaker representing our model
estimator = sagemaker.estimator.Estimator(
    sagemaker_session=sagemaker_session,
    image_name=image_name,
    role=role_arn,
    train_instance_count=1,
    train_instance_type=train_instance_type,
    base_job_name='Weekly-Deepar',
    output_path="s3://" + s3_output_path
)

# Number of datapoints per week. The division by 5 reflects the fact that we aggregated the data by 5 min buckets
one_week_datapoints = 7*(60*24)//5

# Some hyperparameters to tune the training. 
hyperparameters = dict(
    time_freq=data_freq,
    context_length=str(one_week_datapoints), # reflects how many past datapoints are being used during inference 
    prediction_length=str(one_week_datapoints), #reflects how many datapoints we want to predict during inference
    num_cells="40",
    num_layers="3",
    likelihood="gaussian",
    epochs="20",
    mini_batch_size="32",
    learning_rate="0.001",
    dropout_rate="0.05",
    early_stopping_patience="10"
)

estimator.set_hyperparameters(**hyperparameters)

# Channels are a data source abstraction from sagemaker, it just feeds correctly our data during training & testing.
data_channels = {
    "train": "s3://{}/train/".format(s3_data_path),
    "test": "s3://{}/test/".format(s3_data_path)
}

# Run the training job!
estimator.fit(inputs=data_channels)


# Create endpoint
job_name = estimator.latest_training_job.name

image_name = get_image_uri(boto3.Session().region_name, 'forecasting-deepar')

endpoint_name = sagemaker_session.endpoint_from_job(
    job_name=job_name,
    initial_instance_count=1,
    instance_type='ml.m4.xlarge',
    deployment_image=image_name,
    role=role_arn
)

print("Endpoint name:" + endpoint_name)