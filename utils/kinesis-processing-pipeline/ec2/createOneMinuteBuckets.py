import json
import boto3
import datetime
from io import BytesIO
from gzip import GzipFile
from datetime import datetime
# from bson import json_util
from tqdm import tqdm

# new comment
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
bucket = 'fog-bigdata-bmw-data'
my_bucket = s3_resource.Bucket(bucket)
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
table = 'medium_bmw_data_to_kinesis'
kinesis = boto3.client('kinesis', region_name='us-east-1')



metrics = {}

# def myconverter(o):
#     if isinstance(o, datetime.datetime):
#         return o.__str__()

def get_s3_keys(bucket):
    """Get a list of keys in an S3 bucket."""
    keys = []
    # resp = s3.list_objects_v2(Bucket=bucket)
    # # print(json.dumps(resp, default=json_util.default))
    # print(resp['IsTruncated'])
    # for obj in resp['Contents']:
    #     keys.append(obj['Key'])
    # while resp['IsTruncated']:
    #     resp = s3.list_objects_v2(Bucket=bucket)
    #     pass
    for obj in tqdm(my_bucket.objects.filter(Prefix='flowlogs2/AWSLogs/292638641712/vpcflowlogs/')):
        keys.append(obj.key)
    return keys

def writeToDb(metricsInput):
    for key,value in metricsInput.iteritems():
        print(key, value)
        dynamodb.put_item(TableName=table, Item={'id':{'S':key},'value':{'S':str(value)}})


# retrive all files from s3 bucket (their keys)
keys = get_s3_keys(bucket)
print(len(keys))



# iterate over flowlog files (from s3 bucket)
for key in tqdm(keys):
    # print(key)
    # continue
    data = s3.get_object(Bucket=bucket, Key=key)
    bytestream = BytesIO(data['Body'].read())
    got_text = GzipFile(None, 'rb', fileobj=bytestream).read().decode('utf-8')
    lines = got_text.splitlines()[1:] # skip the first line (header)
    if "NODATA" in lines[0]: # skip empty log files
        continue
    # send log data line by line to kinesis stream
    for line in lines:
        lineArray = line.split()
        timestamp = int(lineArray[10])
        timeKey = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M')
        # bucketCount = metrics.get(timeKey)
        # dynamoResponse = dynamodb.get_item(TableName=table, Key={'id':{'S':timeKey}})
        
        # if('Item' in dynamoResponse):
        #     count = dynamoResponse['Item']['value']['S']
        #     count = int(count) + 1
        #     metrics[timeKey] = count
        #     dynamodb.put_item(TableName=table, Item={'id':{'S':timeKey},'value':{'S':str(count)}})
        # else:
        #     count = 1
        #     metrics[timeKey] = count
        #     dynamodb.put_item(TableName=table, Item={'id':{'S':timeKey},'value':{'S':str(count)}})

        if timeKey in metrics:
            metrics[timeKey] = metrics[timeKey] + 1
        else:
            metrics[timeKey] = 1
        # kinesis.put_record(StreamName='medium_VPCFlowLogs', Data=line, PartitionKey='pkey', ExplicitHashKey='123')
        # print(metrics)

print('Writing to database.')
writeToDb(metrics)
print('Success and done.')
# print(metrics)
    # break


