 
import json
from boto3 import client
 
 
lambda_client = client('lambda')
json_body = json.dumps({'message':'Anomalies detected'}) 




invoke_response = lambda_client.invoke(FunctionName="alertDemo",
                                           InvocationType='RequestResponse',
                                           Payload=json_body
                                           )

print(invoke_response['Payload'].read().decode('utf-8'))