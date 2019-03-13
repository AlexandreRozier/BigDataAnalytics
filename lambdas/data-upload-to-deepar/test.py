from lambda_module import lambda_handler

test_event = {
  "Records": [
    {
      "EventSource": "aws:sns",
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:us-east-1:746022503515:s3-logs-object-creation:acfa6ba5-fa2b-4340-8cad-db2d8b76100f",
      "Sns": {
        "Type": "Notification",
        "MessageId": "88d39b2d-48aa-581a-b403-cf80571d6cf5",
        "TopicArn": "arn:aws:sns:us-east-1:746022503515:bmw-push-data",
        "Subject": "Amazon S3 Notification",
        "Message": "{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2019-01-07T09:35:51.291Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:AIDAJ2CJOXH73Y4HB2IYQ\"},\"requestParameters\":{\"sourceIPAddress\":\"10.247.87.210\"},\"responseElements\":{\"x-amz-request-id\":\"0F0419EF97DC9290\",\"x-amz-id-2\":\"uJTuk2WJaqVDK3ts70krDpS3R0gtE6p2X2YYSpw9BB2DmgjpP9LFAAZji+IuNiq5rREjFkJdLWU=\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"ObjectCreationToSNS\",\"bucket\":{\"name\":\"sanitized-datasets\",\"ownerIdentity\":{\"principalId\":\"A1OF5SKISZUEQ9\"},\"arn\":\"arn:aws:s3:::sanitized-datasets\"},\"object\":{\"key\":\"streaming-data-mock/2019-3-13-21-11---2019-3-13-21-26.json\",\"size\":118960,\"eTag\":\"5ec5ea7d381271941524804027a1f4d3\",\"sequencer\":\"005C331D7741D85644\"}}}]}",
        "Timestamp": "2019-01-07T09:35:51.356Z",
        "SignatureVersion": "1",
        "Signature": "okdZWeDwU27cBiEjEzJn9byZCzHKMemN/XHVYiT88i9o924Yp/6dShyK7i7TW2cP64JqrMOHaakjCslavYZjQ+FRWNebkN3YI1fj2eXKvep+kVyHRuESdMXxKWpc8JtDLjhuyFNR+PE8RW/bblARvMH11Ow71hlKmBkNZD9nHR0Xvq8wzU1TjZVsbfLee2mle7L7+H2xoZgaflRXh2xWsEwbVVX1lg22nO1yHGK/LDOSPgG/PC1T11scRN+MhFiznTCXfR+MOYDw3JwXCTk1hDQVgUVDMmFvYc7bFwfTG3PFzZZ0Zx00VnsM2W8ULFho8m7PTV8fgeEBi7UjhDhVFQ==",
        "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-ac565b8b1a6c5d002d285f9598aa1d9b.pem",
        "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:746022503515:s3-logs-object-creation:acfa6ba5-fa2b-4340-8cad-db2d8b76100f",
        "MessageAttributes": {}
      }
    }
  ]
}

lambda_handler(test_event, None)