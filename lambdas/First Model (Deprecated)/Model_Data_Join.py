import boto3
import urllib
import json
import botocore
import time

s3 = boto3.client("s3")
s3_r = boto3.resource('s3')
keys_list = []
json_list = []
timestr = time.strftime("%Y%m%d")



def lambda_handler(event, context):
    
    #Grab the directory with all needed keys (Key is a file)
    list_keys('fog-bigdata-logs', '/streamed2018/12/14/')
    i = 1
    j = 1
    print('Number of Files in this directory = ', len(keys_list))
    
    #Loop to read each key
    for x in keys_list:
        #Connect to S3 and get File name then read it
        file_obj = event["Records"][0]
        print("\n########\n\n",i,"- Filename: ", x)
        #Grab a single key and read it's content
        fileObj = s3.get_object(Bucket = "fog-bigdata-logs", Key='/streamed2018/12/14/' + x)
        file_content = fileObj["Body"].read().decode('utf-8')
        #Number of requests is the number of lines in this file
        requests = len(file_content.split('\n'))
        print("Number of requests = ",requests)
        if i<32:
            json_list.append(tuple((i, requests)))
        i += 1
        # Uncomment this to get file content
        # print(file_content)
        
    #Json dump
    json_result = dump_to_json(json_list)
    # return dump_to_json(json_list)
    return json.loads(json_result)
    
#Function to list keys in a specific bucket according to a prefix
def list_keys(bucket_name, prefix):
    for key in s3.list_objects(Bucket=bucket_name, Prefix=prefix)['Contents']:
        if(key['Key']).endswith('.bucket'):
            keys_list.append(key['Key'].split("/")[-1])

#Function responsible for sending a list of data, converted to json, as a request to the other function that calls the model
def dump_to_json(list):
    
    #change region_name as per the destination lambda function region
    invokeLam = boto3.client("lambda", region_name="us-east-1")
    
    data = {}
    data["data"] = list
    json_data = json.dumps(data)
    
    #Write to json file
    
    file_name = 'json_dumps_{}.json'.format(timestr)
    # file_name = 'json_dumps.json'
    lambda_path = "/tmp/" + file_name
    s3_path = "json_dumps/" + file_name
    s3 = boto3.resource("s3")
    s3.Bucket('fog-bigdata-logs').put_object(Key=s3_path, Body=json_data)
    
    #This will invoke @Marius function, Anomaly Detection.
    resp = invokeLam.invoke(FunctionName = "anomalyDetection", InvocationType = "RequestResponse", Payload = json_data)
    # print(resp["Payload"].read().decode())
    
    print (json_data)
    return(resp["Payload"].read().decode())
    

    