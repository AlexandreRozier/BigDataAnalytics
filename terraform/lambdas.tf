
locals {
  BMWDataPushToDeepAR_zip_path = "${path.module}/../lambdas/bmw-data-stream-to-deepar/lambda.zip"
}
resource "aws_lambda_function" "BMWDataPushToDeepAR" {
  function_name = "BMWDataPushToDeepAR"
  handler       = "lambda.lambda_handler"
  filename      = "${local.BMWDataPushToDeepAR_zip_path}"
  role          = "${aws_iam_role.lambda_sagemaker_invoke.arn}"
  runtime       = "python3.7"
  memory_size   = "384" //mb
  timeout = "45" //s

  environment {
    variables = {
      DEEPAR_ENDPOINT_NAME = "${var.deepar_endpoint_name}"
    }
  }
}

resource "aws_iam_role" "lambda_sagemaker_invoke" {
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
  role       = "${aws_iam_role.lambda_sagemaker_invoke.name}"
  policy_arn = "${data.aws_iam_policy.AmazonS3FullAccess.arn}"
}

resource "aws_iam_role_policy_attachment" "sm-full-access" {
  role       = "${aws_iam_role.lambda_sagemaker_invoke.name}"
  policy_arn = "${data.aws_iam_policy.AmazonSageMakerFullAccess.arn}"
}

/* Lambda function to run inference on deployed model */





