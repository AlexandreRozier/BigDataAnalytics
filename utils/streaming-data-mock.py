import boto3
import s3fs
import pandas as pd
import datetime
from tzlocal import get_localzone as tzlocal
from random import randint
from  datetime import timedelta
import schedule
import time
import logging
import sys


bucket_name = 'fog-datasets'
s3_con = boto3.client('s3')
frequency_min = 15

""" For local debug purpose, redirects logging to stdout
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
root.addHandler(handler)
"""

logging.basicConfig(filename='output.log',level=logging.DEBUG)
logging.info('Starting data streaming, upload frequency: '+str(frequency_min)+'min...')

# Read fixed historical data & generate a Dataframe from it
file_name = 'streaming-data-mock.csv'
data = []
file_str = s3_con.get_object(Bucket=bucket_name, Key=file_name).get('Body').read().decode('utf-8')
df = pd.read_csv('s3:{}/{}'.format(bucket_name,file_name),index_col=[0])
df.index = pd.to_datetime(df.index)
logging.debug(df.head())



def job():
    logging.info('Creating new batch...')
    today = datetime.datetime.today()
    # Select slice of data that should be sent, according to current datetime
    end_time_relative = today.replace(year=2019, month=1, day = 7 + today.weekday() )
    start_time_relative = end_time_relative - timedelta(minutes=frequency_min)
    df_to_send = df[df.index < end_time_relative]
    df_to_send = df_to_send[df_to_send.index > start_time_relative]
    df_to_send.tail()

    datapoints = []
    for time, row in df_to_send.iterrows():
        datapoints.append({'Timestamp':datetime.datetime(time.year,time.month,time.day, time.hour, time.minute, tzinfo=None), 'SampleCount': row.SampleCount, 'Unit': 'None'})

    if(len(datapoints) ==0):
        logging.info("No datapoints! skipping upload...")
        return

    # Upload BMW-like formatted data, in order to trigger the analysis pipeline
    data_bucket_name = 'fog-datasets'
    directory = 'streaming-data-mock'
    e_t = today - timedelta(minutes=frequency_min)
    filename = "{}-{}-{}-{}-{}---{}-{}-{}-{}-{}.json".format(e_t.year,e_t.month,e_t.day,e_t.hour,e_t.minute,today.year,today.month,today.day,today.hour,today.minute)

    logging.info("Appending {} datapoints to {}".format(len(datapoints), filename))
    s3_data_path = "{}/{}/{}".format(data_bucket_name, directory, filename)
    s3filesystem = s3fs.S3FileSystem()

    out = {
        'response-code-200': {'Label': 'response-code-200', 'Datapoints':datapoints}
    }
    try:
        with s3filesystem.open(s3_data_path, 'w') as fp:
            fp.write(repr(out))
    except Exception as e:
        logging.error(e)


schedule.every(frequency_min).minutes.do(job)
while True:
    schedule.run_pending()
    time.sleep(30)

