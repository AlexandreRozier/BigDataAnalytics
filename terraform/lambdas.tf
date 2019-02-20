

variable "deepar_endpoint_name" {} 
variable "mp_endpoint_name" {} 
variable "data_aggregation_frequency" {}
variable "chatbot_url" {}
variable "slack_url" {}
variable "slack_authorization_token" {}

locals {
  DataUploadToDeepAR_zip_path = "${path.module}/../lambdas/data-upload-to-deepar/lambda.zip"
  DataUploadToMP_zip_path = "${path.module}/../lambdas/data-upload-to-mp/lambda.zip"
  ChatbotAlert_zip_path = "${path.module}/../lambdas/chatbot-alert/lambda.zip"
  matplotlib_layer_zip_path = "${path.module}/../lambdas/layers/matplotlib/layer.zip"
  pandas_layer_zip_path = "${path.module}/../lambdas/layers/pandas/layer.zip"
}


resource "aws_lambda_function" "DataUploadToDeepAR" {
  function_name = "DataUploadToDeepAR"
  handler       = "lambda_module.lambda_handler"
  layers = ["${aws_lambda_layer_version.matplotlib_layer.layer_arn}", "${aws_lambda_layer_version.pandas_layer.layer_arn}"]
  filename      = "${local.DataUploadToDeepAR_zip_path}"
  role          = "${aws_iam_role.lambda_sm_s3_role.arn}"
  runtime       = "python3.7"
  memory_size   = "384" //mb
  timeout = "45" //s

  environment {
    variables = {
      ENDPOINT_NAME = "${var.deepar_endpoint_name}"
      DATA_FREQUENCY = "${var.data_aggregation_frequency}"
    }
  }
}


resource "aws_lambda_function" "ChatbotAlert" {
  function_name = "alertDemo"
  handler       = "lambda_module.handler"
  filename      = "${local.ChatbotAlert_zip_path}"
  role          = "${aws_iam_role.lambda_sm_s3_role.arn}"
  runtime       = "nodejs8.10"
  memory_size   = "128" //mb
  timeout = "3" //s
  environment{
    variables ={
      CHATBOX_URL = "${var.chatbot_url}"
      SLACK_URL = "${var.slack_url}"
    }
  }
}


resource "aws_lambda_function" "DataUploadToMP" {
  function_name = "DataUploadToMP"
  handler       = "lambda_module.lambda_handler"
  filename      = "${local.DataUploadToMP_zip_path}"
  layers = ["${aws_lambda_layer_version.matplotlib_layer.layer_arn}", "${aws_lambda_layer_version.pandas_layer.layer_arn}"]
  role          = "${aws_iam_role.lambda_sm_s3_role.arn}"
  runtime       = "python3.7"
  memory_size   = "384" //mb
  timeout = "45" //s

  environment {
    variables = {
      ENDPOINT_NAME = "${var.mp_endpoint_name}"
      SLACK_TOKEN = "${var.slack_authorization_token}"
    }
  }
}

resource "aws_lambda_layer_version" "matplotlib_layer" {
  filename = "${local.matplotlib_layer_zip_path}"
  layer_name = "matplotlib"

  compatible_runtimes = ["python3.7"]
}

resource "aws_lambda_layer_version" "pandas_layer" {
  filename = "${local.pandas_layer_zip_path}"
  layer_name = "pandas"

  compatible_runtimes = ["python3.7"]
}



resource "aws_iam_role" "lambda_sm_s3_role" {
  description="Role giving lambda full access to Lamda, S3 and SageMaker"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}



resource "aws_iam_role_policy_attachment" "s3fa-to-lambda" {
  role       = "${aws_iam_role.lambda_sm_s3_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lafa-to-lambda" {
  role       = "${aws_iam_role.lambda_sm_s3_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaFullAccess"
}


resource "aws_iam_role_policy_attachment" "smfa-to-lambda" {
  role       = "${aws_iam_role.lambda_sm_s3_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}







