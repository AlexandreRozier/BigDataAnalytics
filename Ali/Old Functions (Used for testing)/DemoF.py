import os
import io
import boto3
import json
import csv

# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    data = json.loads(json.dumps(event))
    payload = data['data']
    print(payload)
    
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                       ContentType='text/csv',
                                       Body=payload)
    print(response)
    result = json.loads(response['Body'].read().decode())
    
    # if result['predictions'][0]['score'] < 0.5: 
    #     return 0
    score = result['predictions'][0]['score']
    
    if score > 0.5:
        msg = 'Anomaly detected!'
    else:
        msg = 'Nothing wrong here!'
        
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:746022503515:api-test')
    response = topic.publish(
        # TargetArn='arn:aws:sns:us-east-1:746022503515:api-test',
        Message=json.dumps(dict(
            default=msg
        )),
        Subject='alert',
        MessageStructure='json',
    )
    
    return 1