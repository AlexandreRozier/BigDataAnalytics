

variable "deepar_endpoint_name" {} 
variable "mp_endpoint_name" {} 

locals {
  DataUploadToDeepAR_zip_path = "${path.module}/../lambdas/data-upload-to-deepar/lambda.zip"
  DataUploadToMP_zip_path = "${path.module}/../lambdas/data-upload-to-mp/lambda.zip"
}

/*
resource "aws_lambda_function" "DataUploadToDeepAR" {
  function_name = "DataUploadToDeepAR"
  handler       = "lambda.lambda_handler"
  filename      = "${local.DataUploadToDeepAR_zip_path}"
  role          = "${aws_iam_role.lambda_sm_s3_role.arn}"
  runtime       = "python3.7"
  memory_size   = "384" //mb
  timeout = "45" //s

  environment {
    variables = {
      ENDPOINT_NAME = "${var.deepar_endpoint_name}"
    }
  }
}*/
/*
resource "aws_lambda_function" "DataUploadToMP" {
  function_name = "DataUploadToMP"
  handler       = "lambda.lambda_handler"
  filename      = "${local.DataUploadToMP_zip_path}"
  role          = "${aws_iam_role.lambda_sm_s3_role.arn}"
  runtime       = "python3.7"
  memory_size   = "384" //mb
  timeout = "45" //s

  environment {
    variables = {
      ENDPOINT_NAME = "${var.mp_endpoint_name}"
    }
  }
}


resource "aws_lambda_event_source_mapping" "data-upload-to-mp" {
  event_source_arn = "${aws_sns_topic.bmw-data-upload.arn}"
  function_name    = "${aws_lambda_function.DataUploadToMP.arn}"
}*/
resource "aws_iam_role" "lambda_sm_s3_role" {
  description="Role giving lambda full access to S3 and SageMaker"
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

data "aws_iam_policy" "AmazonS3FullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

data "aws_iam_policy" "AmazonSageMakerFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3-full-access" {
  role       = "${aws_iam_role.lambda_sm_s3_role.name}"
  policy_arn = "${data.aws_iam_policy.AmazonS3FullAccess.arn}"
}

resource "aws_iam_role_policy_attachment" "sm-full-access" {
  role       = "${aws_iam_role.lambda_sm_s3_role.name}"
  policy_arn = "${data.aws_iam_policy.AmazonSageMakerFullAccess.arn}"
}

/* Lambda function to run inference on deployed model */





