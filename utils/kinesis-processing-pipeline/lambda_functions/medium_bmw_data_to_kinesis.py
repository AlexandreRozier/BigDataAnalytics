import json
import boto3
from io import BytesIO
from gzip import GzipFile
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
table = 'medium_bmw_data_to_kinesis'
kinesis = boto3.client('kinesis', region_name='us-east-1')

def lambda_handler(event, context):
    bucket = 'fog-bigdata-bmw-data'
    metrics = {}
    
    try:
        # retrive all files from s3 bucket (their keys)
        keys = get_s3_keys(bucket)
        # iterate over flowlog files (from s3 bucket)
        for key in keys:
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
                bucketCount = metrics.get(timeKey)
                dynamoResponse = dynamodb.get_item(TableName=table, Key={'id':{'S':timeKey}})
                
                if('Item' in dynamoResponse):
                    count = dynamoResponse['Item']['value']['S']
                    count = int(count) + 1
                    metrics[timeKey] = count
                    dynamodb.put_item(TableName=table, Item={'id':{'S':timeKey},'value':{'S':str(count)}})
                else:
                    count = 1
                    metrics[timeKey] = count
                    dynamodb.put_item(TableName=table, Item={'id':{'S':timeKey},'value':{'S':str(count)}})
                kinesis.put_record(StreamName='medium_VPCFlowLogs', Data=line, PartitionKey='pkey', ExplicitHashKey='123')
            print(metrics)
            # return key
            
    
    except Exception as e:
        print(e)
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def get_s3_keys(bucket):
    """Get a list of keys in an S3 bucket."""
    keys = []
    resp = s3.list_objects_v2(Bucket=bucket)
    for obj in resp['Contents']:
        keys.append(obj['Key'])
    return keys
