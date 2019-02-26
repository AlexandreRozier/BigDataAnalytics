import os
import io
import boto3
import json
# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    data = json.loads(json.dumps(event))
    payload = data['data']
    # Convert the data to csv format
    payload = list(map(lambda d: str.join(',',map(str,d)), payload))
    payload = str.join('\n',payload)
    
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                       ContentType='text/csv',
                                       Body=payload)
    
    # Parse the csv response
    res_str = response['Body'].read().decode("utf-8")
    predictions = list(map(lambda st: st == 'True',str.split(res_str,'\n')[:-1]))
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:746022503515:api-test')
    
    response = topic.publish(
        # TargetArn='arn:aws:sns:us-east-1:746022503515:api-test',
        Message=json.dumps(dict(
            default=str(predictions)
        )),
        Subject='alert',
        MessageStructure='json',
    )
    
    return predictions