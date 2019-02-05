import boto3 
import datetime
import json
import logging 
s3 = boto3.client('s3')

def get_matching_s3_keys(bucket, prefix='', suffix=''):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    kwargs = {'Bucket': bucket}

    # If the prefix is a single string (not a tuple of strings), we can
    # do the filtering directly in the S3 API.
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix

    while True:

        # The S3 API response is a large blob of metadata.
        # 'Contents' contains information about the listed objects.
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            key = obj['Key']
            if key.startswith(prefix) and key.endswith(suffix):
                yield key

        # The S3 API is paginated, returning up to 1000 keys at a time.
        # Pass the continuation token into the next response, until we
        # reach the final page (when this field is missing).
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

countByDate = {}
bucket = 'fog-bigdata-logs'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
s3_resource = boto3.resource('s3')

for key in get_matching_s3_keys(bucket=bucket, prefix="/streamed2019" ,suffix='.bucket'):
    key_splitted = key.split("/")
    year = int(key_splitted[-4][8:])
    month = int(key_splitted[-3])
    day = int(key_splitted[-2])
    hour = int(key_splitted[-1].split("-")[0])
    minute = int(key_splitted[-1].split("-")[1][:-7])
    date = datetime.datetime(year=year,month=month,day=day,hour=hour,minute=minute)

    obj = s3_resource.Object(bucket, key)
    # read the file contents in memory
    read = obj.get()["Body"].read()
    countByDate[str(date.timestamp)]= str(read).count("\n")
    print("Processed key: "+key)

# Write complete dataset

s3_resource.Object('fog-datasets', 'flowlogs-aggregated-per-10-min').put(Body=json.dumps(countByDate))
