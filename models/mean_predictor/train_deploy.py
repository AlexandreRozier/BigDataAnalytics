import boto3
import re
import os
import numpy as np
import pandas as pd
import sagemaker as sage
from time import gmtime, strftime
from sagemaker.predictor import json_serializer
import argparse
import sys, os

'''
Takes the ECR image provided in --imagename, creates a training job
and deploys the model on an endpoint
'''

parser = argparse.ArgumentParser(description='train and deploy the mean predictor model with AWS sagemaker')
parser.add_argument('--trainpath', nargs=1, default='s3://fog-datasets/rcf/data/train/data.csv',
                    help='AWS S3 path of training data')
parser.add_argument('--role', nargs=1, default='arn:aws:iam::746022503515:role/sage_maker',
                    help='AWS IAM role for usage with sagemaker')
parser.add_argument('--outpath', nargs=1, default='s3://mean-predictor/output',
                    help='AWS S3 path for training output logs')
parser.add_argument('--name', nargs=1, default='mean-predictor', help='Name of docker image in AWS ECR')          
parser.add_argument('--freq', nargs=1, default='5min',
                    help='frequency to use for predictions')
parser.add_argument('--update', nargs=1, type=bool, default=False,
                    help='''
                    Wether to create a new endpoint or update the existing one. 
                    Sagemaker will crash if you try to update a non existent endpoint''')

if __name__ == '__main__':
  args = parser.parse_args()

  sess = sage.Session()

  account = sess.boto_session.client('sts').get_caller_identity()['Account']
  region = sess.boto_session.region_name
  image = '{}.dkr.ecr.{}.amazonaws.com/{}:latest'.format(account, region, args.name)

  hyperparams = dict(freq='5min')

  # Create a training job for the model
  mean_predictor = sage.estimator.Estimator(
    image,
    args.role, 1, 'ml.m5.large',
    output_path=args.outpath,
    sagemaker_session=sess,
    hyperparameters=dict(freq=args.freq)
  )

  mean_predictor.fit(args.trainpath)

  # Deploy the model as sagemaker endpoint
  predictor = mean_predictor.deploy(
    1, 
    'ml.t2.medium',
    endpoint_name=args.name,
    update_endpoint=True,
    serializer=json_serializer
  )
