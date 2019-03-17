import json
import boto3
import csv
from io import BytesIO
from gzip import GzipFile
from datetime import datetime


dynamodb = boto3.client('dynamodb')
table = 'medium_bmw_data_to_kinesis'
kinesis = boto3.client('kinesis', region_name='us-east-1')

def lambda_handler(event, context):

    # read from csv
    with open('medium_bmw_data_to_kinesis_weekdays.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        count = 0
        for row in readCSV:
            if count > 0:
                row = row[0].split(';')
                dateMinuteInt = row[0];
                dateMinuteInt = dateMinuteInt.replace("_","")
                dateMinuteInt = dateMinuteInt.replace("-","")
                data = {
                    'dateminute': dateMinuteInt,
                    'numberOfRequests': row[1],
                    'weekdayString': row[2],
                    'weekdayId': row[3],
                }
                dataString = json.dumps(data)
                # print(dataString)
                kinesis.put_record(StreamName='medium_VPCFlowLogs', Data=dataString, PartitionKey='pkey', ExplicitHashKey='123')
                # if count > 5:
                    # break
            count += 1
    
    # send data to kinesis