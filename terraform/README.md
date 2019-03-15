
# Pipeline provisioning with Terraform
## Pipeline overview
We put a special effort into providing a straightforward terraform-based provisioning script. 

It will spin up the following infrastructure:
- S3 buckets to put data preprocess correctly for use by our models
- Train & export as endpoints a DeepAR and a MeanPredictor model
- All IAM roles & policies
- EC2 instance mocking a continous data stream
- SNS Topics triggering events on arrival of this stream 
- Lambda functions listening on these SNS Events and asking both models for predictions and anomaly detection

A more thorough explanation of the pipeline can be found in section 3 of our LaTeX report.


## Provisioning steps

- Log to aws cli with correct account & region (`aws configure`)
- Activate correct venv
    - `conda env create -f ./environment.yml --name big-data-analytics`
    -  `conda activate big-data-analytics`

- Fill up `terraform.tfvars` with your own credentials & preferences
- Run `terraform init`

- Run terraform plan
- Check output
- Run terraform apply  
>**Warning:** Since terraform apply spins up the whole infrastructure and trains our various models, it is expected to run during ~2H. You can speed this up by specifying a beefier `train_instance_type` in the `train_deploy` scripts.  

- Finally, add triggers to lambdas from the web interface (make `DataUploadToDeepAR` and `DataUploadToMP` subscribe to the SNS Topic `data-upload`). This is mandatory since Terraform does not support lambda subscription to SNS topics yet.
