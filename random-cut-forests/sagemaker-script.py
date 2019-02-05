import boto3
import botocore
import sagemaker
import sys
import pickle
from io import BytesIO
from sagemaker import RandomCutForest

bucket = 'fog-datasets'   # <--- specify a bucket you have access to
prefix = 'rcf/benchmarks'
execution_role = 'arn:aws:iam::746022503515:role/sage_maker'

s3_client = boto3.client('s3')

# check if the bucket exists
try:
    s3_client.head_bucket(Bucket=bucket)
except botocore.exceptions.ParamValidationError as e:
    print('Hey! You either forgot to specify your S3 bucket'
          ' or you gave your bucket an invalid name!')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == '403':
        print("Hey! You don't have permission to access the bucket, {}.".format(bucket))
    elif e.response['Error']['Code'] == '404':
        print("Hey! Your bucket, {}, doesn't exist!".format(bucket))
    else:
        raise
else:
    print('Training input/output will be stored in: s3://{}/{}'.format(bucket, prefix))

data_key = 'rcf/bmw-data-enriched.p'

s3 = boto3.resource('s3')
data = {}
with BytesIO() as data:
    s3.Bucket(bucket).download_fileobj(data_key, data)
    data.seek(0)    # move back to the beginning after writing
    data = pickle.load(data)



session = sagemaker.Session()

# specify general training job information
rcf = RandomCutForest(role=execution_role,
                      train_instance_count=1,
                      train_instance_type='ml.m4.xlarge',
                      data_location='s3://{}/{}/'.format(bucket, prefix),
                      output_path='s3://{}/{}/output'.format(bucket, prefix),
                      num_samples_per_tree=512,
                      num_trees=50)

# automatically upload the training data to S3 and run the training job
rcf.fit(rcf.record_set(taxi_data.value.as_matrix().reshape(-1,1)))
