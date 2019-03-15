# Big Data Analytics: Out-of-the-box AWS time series processing pipeline

This repository hosts a terraform-managed AWS-based time series processing pipeline. We took special care of making it compatible with [AWS VPC Flowlogs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html).



## What it does

Set up a whole time series analysis pipeline on AWS, training two models for prediction and anomaly detection:
- AWS's [DeepAR](https://docs.aws.amazon.com/sagemaker/latest/dg/deepar.html) time series prediction model
- AWS's [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) anomaly detection model
- A baseline own algorithm of our own, based on mean +/- standard deviation, used for both prediction & anomaly detection

## Repository structure

### `lambdas/`

Hosts the code of our AWS lambda functions. These services are triggered by AWS SNS Topic events, usually upon arrival of new batches of data, and are charged with contacting our trained models for prediction & anomaly detection. 

### `mock_data/`

Hosts our mock data, used to test our models locally before plugging them to the whole pipeline.

### `models/`

Scripts to train & deploy our models as SageMaker endpoints.

### `terraform/`

Terraform-based provisioning scripts, taking care of everything from spinning up AWS services to training and deploying our models. Basically a on-click deployment solution!

### `utils/`

Utility scripts used to generate & preprocess data.