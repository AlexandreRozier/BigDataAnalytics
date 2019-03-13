import json
import boto3
import os
import pandas as pd
import datetime
from datetime import timedelta
import logging
import json
import numpy as np
from dateutil.tz import tzlocal
import io
import requests
from matplotlib import pyplot as plt

endpoint_name = os.environ.get('ENDPOINT_NAME')
data_freq = os.environ['DATA_FREQUENCY']


def series_to_obj(ts, dynamic_feats=None, cat=None):
    """
    dynamic_feats: [[]]
    """
    obj = {"start": str(ts.index[0]), "target": list(ts), "dynamic_feat":dynamic_feats}
    if cat is not None:
        obj["cat"] = cat
    return obj

def series_to_jsonline(ts, dynamic_feats=None, cat=None):
    return json.dumps(series_to_obj(ts, dynamic_feats, cat))

class DeepARPredictor():

    def set_prediction_parameters(self, freq, prediction_length):
        """Set the time frequency and prediction length parameters. This method **must** be called
        before being able to use `predict`.
        
        Parameters:
        freq -- string indicating the time frequency
        prediction_length -- integer, number of predicted time points
        
        Return value: none.
        """
        self.freq = freq
        self.prediction_length = prediction_length
        
    def predict(self, ts, dynamic_feats_per_series, runtime, cat=None, encoding="utf-8", num_samples=100, quantiles=["0.1", "0.5", "0.9"]):
        """Requests the prediction of for the time series listed in `ts`, each with the (optional)
        corresponding category listed in `cat`.
        
        Parameters:
        ts -- list of `pandas.Series` objects, the time series to predict
        cat -- list of integers (default: None)
        encoding -- string, encoding to use for the request (default: "utf-8")
        num_samples -- integer, number of samples to compute at prediction time (default: 100)
        quantiles -- list of strings specifying the quantiles to compute (default: ["0.1", "0.5", "0.9"])
        
        Return value: list of `pandas.DataFrame` objects, each containing the predictions
        """
        prediction_times = [x.index[-1]+1 for x in ts]
        req = self.__encode_request(ts, dynamic_feats_per_series, cat, encoding, num_samples, quantiles)
        res = runtime.invoke_endpoint(EndpointName=endpoint_name,
                                       ContentType='application/json',
                                       Body=req)
        return self.__decode_response(res, prediction_times, encoding)
    
    def __encode_request(self, ts, dynamic_feats_per_series,cat, encoding, num_samples, quantiles):
        instances = [series_to_obj(ts[k], dynamic_feats_per_series[k] if dynamic_feats_per_series else None, cat[k] if cat else None) for k in range(len(ts))]
        configuration = {"num_samples": num_samples, "output_types": ["quantiles"], "quantiles": quantiles}
        http_request_data = {"instances": instances, "configuration": configuration}
        return json.dumps(http_request_data).encode(encoding)
    
    def __decode_response(self, response, prediction_times, encoding):
        response_data = json.loads(response['Body'].read().decode(encoding))
        list_of_df = []
        for k in range(len(prediction_times)):
            prediction_index = pd.DatetimeIndex(start=prediction_times[k], freq=self.freq, periods=self.prediction_length)
            list_of_df.append(pd.DataFrame(data=response_data['predictions'][k]['quantiles'], index=prediction_index))
        return list_of_df


def lambda_handler(event, context):

    # LOGGING to cloudwatch
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.debug(json.dumps(event))

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
    serie = serie.groupby([pd.Grouper(freq=data_freq)]).sum()
 
    logger.debug(serie)
    runtime= boto3.client('runtime.sagemaker')
  
    n_3h_datapoints = (60*24*7)//5
    
    predictor = DeepARPredictor()
    predictor.set_prediction_parameters(data_freq, n_3h_datapoints)
     
    # Create feature series of holidays
    end_of_holiday = datetime.date(2019, 1, 7)
    #holidays_data = [1 if time < pd.Timestamp(end_of_holiday,tz=None) else 0  for time in serie.index]
    #holidays_feature_serie = pd.Series(data=holidays_data, index=serie.index)
    
    # Create feature series of weekdays
    weekends_date = [0 if time.weekday() < 5 else 1 for time in serie.index]
    weekends_feature_series = pd.Series(data=weekends_date, index=serie.index)

    predictions = predictor.predict([serie], 
        [[
            #list(holidays_feature_serie)+[0 for i in range(n_3h_datapoints)],
            list(weekends_feature_series)+[0 if (serie.index[-1] + timedelta(minutes=k*5)).weekday() < 5 else 1 for k in range(n_3h_datapoints)],
        ]], runtime)
                                       
    logger.info(predictions)
    
    payload={
      "title":"Live prediction",
      "initial_comment":"Detected new data batch. You'll find below the resulting weekly-forecast.",
      "filename":"buf.png",
      "token":"xoxp-463923555735-464821849926-544895594565-795f5333d4821f875dcd5e128a17abd8",
      "channels":['#aws'],
    }
    
    k=0
    ax = predictions[k]['0.5'].plot(label='prediction median', figsize=(12,6))
    p10 = predictions[k]['0.1']
    p90 = predictions[k]['0.9']
    ax.fill_between(p10.index, p10, p90, color='y', alpha=0.5, label='80% confidence interval')
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
  
    
    return 

       


