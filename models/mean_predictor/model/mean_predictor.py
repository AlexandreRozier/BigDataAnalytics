import numpy as np
import pandas as pd

class MeanPredictor():
    
    def __init__(self, freq='5min'):
        self.freq = freq
        
    def fit(self,x,square_deviation=True):
        x_group = x.groupby(np.array(list(map(self.__time_hash,x.index))).T.tolist())
        x_mean = x_group.mean()
        self.mean_dict = dict(zip(list(x_mean.index),x_mean.values.flatten()))
        if square_deviation:
            x_std_dist = x_group.std().values.squeeze()
        else:
            x_std_dist = np.array([np.abs(df.values - self.mean_dict[idx]).mean() for idx,df in list(x_group)])
        self.std_dict = dict(zip(list(x_mean.index),x_std_dist))
    
    def __time_hash(self,t):
        return (t.weekday() < 5,t.hour,t.minute)
    
    def __predict(self,t):
        t_hash = self.__time_hash(t)
        return self.mean_dict[t_hash], self.std_dict[t_hash]
    
    def __getitem__(self,t):
        if type(t) is slice:
            assert type(t.start) is pd.Timestamp
            assert type(t.stop) is pd.Timestamp
            assert t.step is None or type(t.step) is int
            step = t.step if type(t.step) is int else 1
            time_range = pd.date_range(t.start,t.stop,freq=self.freq)[::t.step]
            predictions = list(map(self.__predict,time_range))
            return pd.DataFrame(index=time_range,data=predictions,columns=['Value','Std'])
        else:
            assert t is pd.Timestamp
    

