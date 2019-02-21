import json
import boto3
import os   
import pandas as pd
import datetime
from datetime import timedelta
import logging  
import botocore 
import json
import numpy as np
from dateutil.tz import tzlocal
from matplotlib import pyplot as plt
import io
import requests
import sys

def lambda_handler(event, context):


    # LOGGING to cloudwatch
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.debug(json.dumps(event))


    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
         msg = json.loads(event["Records"][0]["Sns"]["Message"])
    except Exception as e:
        logger.error("Failed to parse msg:"+e)
        raise e
    record = msg["Records"][0]
    logger.debug(record)
    
    bucket_name = record['s3']['bucket']['name']
    key = record['s3']['object']['key'] 
    
    logger.debug(bucket_name)
    logger.debug(key)
    
    s3_con = boto3.client('s3')
  
    
    data = []
    file_str = s3_con.get_object(Bucket=bucket_name, Key=key).get('Body').read().decode('utf-8')
    batch = eval(file_str)
    if 'response-code-200' in batch.keys():
        data = data + batch['response-code-200']['Datapoints']
    
 
    logger.debug(data)


    df = pd.DataFrame(data)
    df = df.drop(columns=['Unit'])
    df = df.groupby('Timestamp').sum()
    serie = pd.Series(data=df.SampleCount.values, index=[i.replace(tzinfo=None) for i in pd.to_datetime(df.index)])
    serie = serie.sort_index()
    start_date = serie.index[0] - timedelta(minutes=5)
    end_date = serie.index[-1] + timedelta(minutes=5)
    format = "%Y-%m-%d %H:%M:%S"
    
    # Runs anomaly detection
    http_request_data = {"start": start_date.strftime(format), "end": end_date.strftime(format)}
    body = json.dumps(http_request_data).encode('utf-8')
    runtime= boto3.client('runtime.sagemaker')
    
    res = runtime.invoke_endpoint(EndpointName=os.environ['ENDPOINT_NAME'],
                                       ContentType='application/json',
                                       Body=body)
    logger.debug(res)                                   
    res = pd.read_csv(io.BytesIO(res['Body'].read()), encoding='utf8')
    res = res.set_index('Timestamp')
    res.index = pd.to_datetime(res.index)
    logger.debug(res)

    anomalies_idx = []
    for time, count in serie.iteritems():
        row = res.iloc[res.index.get_loc(time, method='nearest')]

        mean = row['Value']
        std = row['Std']
        if(count < mean - std or count > mean + std ):
            anomalies_idx.append(time)

    anomalies_series = serie[anomalies_idx]
    if(not anomalies_series.empty):
    
        payload={
            "title":"Live anomaly detection",
            "initial_comment":"Detected new data batch. You'll find below the result of our anomaly.",
            "filename":"buf.png",
            "token":"xoxp-463923555735-464821849926-544895594565-795f5333d4821f875dcd5e128a17abd8",
            "channels":['#aws'],
        }
        
        ax = res['Value'].plot(label='prediction median', figsize=(12,6))
        p10 = res['Value']-res['Std']
        p90 = res['Value']+res['Std']
        ax.fill_between(p10.index, p10, p90, color='y', alpha=0.5, label='Normal behavior area')
        anomalies_series.plot(
            style=['.'],
            label='Anomalies',
            ax = ax)
        ax.legend()


        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        my_file = {
        'file' : ('./buf.jpg', buf, 'png')
        }
        r = requests.post("https://slack.com/api/files.upload", params=payload, files=my_file)
        buf.close()
        plt.cla()
    

    # Runs prediction detection
    logger.info("Running prediction...")
    http_request_data = {"start": serie.index[-1].strftime(format), "end": (serie.index[-1] + timedelta(hours=3)).strftime(format)}
    body = json.dumps(http_request_data).encode('utf-8')
    
    res = runtime.invoke_endpoint(EndpointName='mean-predictor',
                                       ContentType='application/json',
                                       Body=body)
    res = pd.read_csv(io.BytesIO(res['Body'].read()), encoding='utf8')
    res = res.set_index('Timestamp')
    res.index = pd.to_datetime(res.index)
    logger.debug(res)

    payload={
            "title":"Live 3h forecast",
            "initial_comment":"Detected new data batch. You'll find below our 3h forecast.",
            "filename":"buf2.png",
            "token":"xoxp-463923555735-464821849926-544895594565-795f5333d4821f875dcd5e128a17abd8",
            "channels":['#aws'],
    }
    
    ax = res['Value'].plot(label='prediction median', figsize=(12,6))
    p10 = res['Value']-res['Std']
    p90 = res['Value']+res['Std']
    ax.fill_between(p10.index, p10, p90, color='y', alpha=0.5, label='Average Standard Deviation')
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    my_file = {
    'file' : ('./buf2.jpg', buf, 'png')
    }
    r = requests.post("https://slack.com/api/files.upload", params=payload, files=my_file)
    buf.close()
    plt.cla()

    
    return 

       


