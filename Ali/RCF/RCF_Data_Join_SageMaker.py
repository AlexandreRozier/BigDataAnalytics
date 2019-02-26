import boto3
import urllib
import json
import botocore
import time

s3 = boto3.client("s3")
s3_r = boto3.resource('s3')
keys_list = []
csv_list = []
del_date_list = []
timestr = time.strftime("%Y%m%d---%H:%M:%S")



def lambda_handler(event, context):
    
    list_keys('rcf-sagemaker-testdata')
    i = 1
    j = 1
    print('Number of Files in this directory = ', len(keys_list))
    # for x in keys_list:
        
    #Connect to S3 and get File name then read it
    file_obj = event["Records"][0]

    print("\n########\n\n",i,"-Filename:", keys_list[0])

    #Grab the file
    fileObj = s3.get_object(Bucket = "rcf-sagemaker-testdata", Key=keys_list[0])

    #Read File Content
    file_content = fileObj["Body"].read().decode('utf-8')

    #Get Number Of lines
    num_lines = len(file_content.split('\n'))
        
    print("\n\tNumber of Lines=",num_lines)
        
    #Split the whole file into lines, in a list
    sum_values_list = file_content.splitlines()
        
    #Remove the date from each element inside the list
    sum_list(sum_values_list)
    del_date(sum_values_list)
        
        # i += 1
    copy_to_bucket('rcf-sagemaker-testdata','rcf-sagemaker-finished', keys_list[0])
    
     #Json dump
    json_result =  dump_to_csv(del_date_list)
    # return dump_to_json(json_list)
    return json.loads(json_result)

    
#Remove date from elements taking comma as a delimeter
def sum_list(list):
    for item in list:
        # csv_list.append(item.split(",")[-1])
        csv_list.append(item)
        
#Remove date from elements taking comma as a delimeter
def del_date(list):
    for item in list:
        del_date_list.append(item.split(",")[-1])

        
def copy_to_bucket(bucket_from_name, bucket_to_name, file_name):
    copy_source = {
        'Bucket': bucket_from_name,
        'Key': file_name
    }
    s3_r.Object(bucket_to_name,"Data Finished at {} --> ".format(timestr) + file_name).copy_from(CopySource=bucket_from_name + "/" + file_name)
    # s3_r.Object(bucket_to_name, file_name).copy(copy_source)
    s3_r.Object(bucket_from_name,file_name).delete()


def print_list(list):
    for element in list:
        print(element)
    
#Get list of keys
def list_keys(bucket_name):
    for key in s3.list_objects(Bucket=bucket_name)['Contents']:
        if(key['Key']).endswith('.csv'):
            keys_list.append(key['Key'].split("/")[-1])

#Generates json files and sends them to a lambda function containing another model call
def dump_to_csv(list):
    
    #change region_name as per the destination lambda function region
    invokeLam = boto3.client("lambda", region_name="us-east-1")
    
    data = "\n".join(list)
    
    #Write to csv file
    file_name = 'csv_dumps_{}.csv'.format(timestr)
    lambda_path = "/tmp/" + file_name
    s3_path = "csv_dumps/" + file_name
    s3 = boto3.resource("s3")
    s3.Bucket('rcf-sagemaker-finished').put_object(Key=s3_path, Body=data)
        
    #This will invoke @Nursulta's function, RCF Anomaly Detection.
    resp = invokeLam.invoke(FunctionName = "RCF_Anomaly_Model_2", InvocationType = "RequestResponse", Payload = parse_to_json(csv_list))
    # print(resp["Payload"].read().decode())
    
    # print ("\n\nAll Sum Data from CSV function:\n", data)
    return(resp["Payload"].read().decode())
    
#Request to model needs to be a json
def parse_to_json(objects):
   
    # objects = [float(i) for i in objects]
    data = {}
    data["data"] = objects
    json_data = json.dumps(data)
    # print (json_data)
    return json_data
