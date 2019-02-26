import os
import io
import boto3
import numpy
import json
import csv
import pandas as pd
from pandas import Series
from datetime import datetime
import matplotlib.pyplot as plt
import requests
 
# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

payload_2={
  "title":"RCF Anomaly Detection",
  "initial_comment":"Detected Anomalies based on cut-off threshold",
  "filename":"buf.png",
  "token":"xoxp-463923555735-465241688214-545340537876-0d53b600191cf0737664d1595e079c0c",
  "channels":['#aws'],
}

score_array = []

def lambda_handler(event, context):
    
    payload = event
    # print(payload)
    
    #get the response from the model endpoint
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                      ContentType='text/csv',
                                      Body=print_list(payload))
    
    # Parse the csv response
    res_str = response['Body'].read().decode("utf-8")
    data = json.loads(res_str)
    debugging_message="\n\n######\n\nScores response from the model for debugging:\n\n" + res_str + "\n\n"
    # print(debugging_message)
    for item in data['scores']:
        score_array.append(item['score'])
    # print("\n\n######\n\nData after parsing, for RCF Calculation:\n\n",score_array)
    
    #Calculate cut-off final score
    scores_array = numpy.array(score_array)
    score_mean = scores_array.mean()
    score_std = scores_array.std()
    score_cutoff = score_mean + 3*score_std

    cut_off_final_score=('Cut-Off final Score:',score_cutoff)
    cut_off_final_score_debugging=('Cut-Off final score:',score_cutoff)

    #Send Slack MSG
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:746022503515:RCF-SageMaker')
    
    response = topic.publish(
        Message=str("Final Cut-Off Score: {}".format(score_cutoff)),
        Subject='#aws',
        MessageStructure='text/plain',
    )
    
    response = topic.publish(
        Message=str(compare_cut_off(score_cutoff,payload)),
        Subject='#aws',
        MessageStructure='text/plain',
    )

    plot_send(payload, score_cutoff, score_array)

    # print("\n\n######\n\n", cut_off_final_score_debugging,"\n\n######\n\n") 
    # return (cut_off_final_score) 
    return (compare_cut_off(score_cutoff,payload))
    
def print_list(list):
    string = ""
    for element in list['data']:
        string = "\n".join([string,str(element.split(",")[1])])
    return string

def compare_cut_off(response_here, list_here):
    print("Final Cut-Off Scores with TIMESTAMP + Score: \n")
    i = 0
    string_2 = ""
    for items in list_here['data']:
        if float(score_array[i]) > response_here:
            # print(str(items.split(",")[0]), float(score_array[i]))
            string_2 = "---".join([str(items.split(",")[0]), str(score_array[i])])
        i += 1    
    return ("Anomalies found --> TIMESTAMP + Score:",string_2)

def print_payload(payload):
    # print(payload)
    for item in payload['data']:
        print(str(item.split(",")[0]), float(item.split(",")[1]))

def plot_send(dataFile, anomaly_score, array_results):
    
    x=[]
    y=[]
    i=0
    data = json.dumps(dataFile['data'])
    
    df=pd.read_json(data)
    df.to_csv('/tmp/results.csv', index=False, header = 0)
    
    with open('/tmp/results.csv', 'r') as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        for row in reader:
            # print((row[0].split(',')[0]))
            x.append(datetime.strptime((row[0].split(',')[0]), '%Y-%m-%d %H:%M:%S'))
            y.append(float((row[0].split(',')[1])))
            if array_results[i] > anomaly_score:
                plt.plot([datetime.strptime((row[0].split(',')[0]), '%Y-%m-%d %H:%M:%S')], [array_results[i]], marker='o', markersize=3, color="black", label='Anomalies')
            i += 1
        
    plt.plot(x,y)
    plt.axhline(y=anomaly_score, color='r', linestyle='-', label='Threshold')
    
    plt.title('Data from CSV: TimepStamps and Scores')

    plt.xlabel('TimeStamps')
    plt.ylabel('Scores')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    my_file = {
      'file' : ('./buf.png', buf, 'png')
    }
    r = requests.post("https://slack.com/api/files.upload", params=payload_2, files=my_file)
    buf.close()
    plt.cla()
  