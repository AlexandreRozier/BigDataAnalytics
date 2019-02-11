import boto3 
import s3fs
import pandas as pd
import datetime
from tzlocal import get_localzone as tzlocal
import boto3
from random import randint
from  datetime import datetime
bucket_name = 'fog-datasets'
s3_con = boto3.client('s3')

file_name = 'streaming-data-mock.csv'
data = []
file_str = s3_con.get_object(Bucket=bucket_name, Key=file_name).get('Body').read().decode('utf-8')
df = pd.read_csv('s3:{}/{}'.format(bucket_name,file_name))

# uploader toutes les 5 min un nb ~ random d'elts 
today = datetime.today()
print(today)