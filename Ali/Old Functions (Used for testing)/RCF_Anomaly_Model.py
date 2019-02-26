import os
import io
import boto3
# import numpy
import json
 
# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')


score_array = []

def lambda_handler(event, context):
    
    payload = event
    # Convert the Data to csv format
    print(payload)
    #get the response from the model endpoint
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                      ContentType='text/csv',
                                      Body=print_list(payload))
    
    # Parse the csv response
    res_str = response['Body'].read().decode("utf-8")
    data = json.loads(res_str)
    print("\n\nScores response from the model for debugging:\n\n",res_str,"\n\n")
    for item in data['scores']:
        score_array.append(item['score'])
        
    print("\n\nData after parsing, for RCF Calculation:",score_array)
    return ("\n\nData after parsing, for RCF Calculation:",score_array)
    
    # #Calculate cut-off final score
    # scores_array = numpy.array(score_array)
    # score_mean = scores_array.mean()
    # score_std = scores_array.std()
    # score_cutoff = score_mean + 3*score_std

    # print("\n\n######\n\n\Cut-Off final score:",score_cutoff) 
    # return ("\n\n######\n\n\Cut-Off final score:",score_cutoff) 
    
def print_list(list):
    string = ""
    for element in list['data']:
        string = "\n".join([string,str(element)])
    return string