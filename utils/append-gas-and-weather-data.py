import json 
import datetime
import pickle
from tzlocal import get_localzone as tzlocal
from scipy.stats import norm
import random

"""
'Datapoints': [{
    'Timestamp': datetime.datetime(2018, 12, 25, 17, 10, tzinfo = tzlocal()),
    'Sum': 79792.0,
    'Unit': 'None'
}
"""
weather_conditions = ['Sun', 'Clouds', 'Rain', 'Snow']

with open("data.p", 'r+b') as outfile:
    data = pickle.load(outfile)
    for key, val in data.items():
        print("Processing: "+key)
        for pt in val['Datapoints']:
            pt['Temperature'] = norm.rvs(size=1,loc=20,scale=4)[0]
            pt['Weather'] = random.choice(weather_conditions)
            pt['Gas price'] = norm.rvs(size=1,loc=1.70,scale=0.10)[0]
    
    print(data)
    pickle.dump(data, outfile)
