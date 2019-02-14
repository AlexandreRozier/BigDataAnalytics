# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function

import os
import json
import pickle
import StringIO
import sys
import signal
import traceback
import flask

import pandas as pd

prefix = '/opt/ml/'
model_path = os.path.join(prefix, 'model', 'model.pkl')
# A singleton for holding the model. This simply loads the model and holds it.
# It has a predict function that does a prediction based on the model and the input data.

class FormatException(Exception):
    pass

class ScoringService(object):
    model = None                # Where we keep the model when it's loaded

    @classmethod
    def get_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self.model == None:
            with open(model_path, 'r') as inp:
                self.model = pickle.load(inp)
        return self.model

    @classmethod
    def predict(self, req):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        model = self.get_model()
        if req.get('start') is None or req.get('end') is None:
            raise FormatException()
        try:
            start = pd.Timestamp(req['start'])
            end = pd.Timestamp(req['end'])
        except ValueError:
            raise FormatException()
        return model[start:end:1]

# The flask app for serving predictions
app = flask.Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    health = ScoringService.get_model() is not None  # You can insert a health check here

    status = 200 if health else 404
    return flask.Response(response='\n', status=status, mimetype='application/json')

@app.route('/invocations', methods=['POST'])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    try:
        if not flask.request.content_type in ['text/json','application/json']:
            raise FormatException()

        data = flask.request.data.decode('utf-8')
        req_dict = json.loads(data)

        # Do the prediction
        predictions = ScoringService.predict(req_dict)
        # Convert from numpy back to CSV
        out = StringIO.StringIO()
        predictions.to_csv(out, header=True, index=True)
        result = out.getvalue()
    except FormatException:
        return send_instructions()

    return flask.Response(response=result, status=200, mimetype='text/csv')

def send_instructions():
    error_msg = """
    Required text/json with format:\n
    {\n
        "start": "YYYY-MM-DD HH:MM:00",\n
        "end": YYYY-MM-DD HH:MM:00\n
    }\n
    """
    return flask.Response(response=error_msg, status=415, mimetype='text/plain')

