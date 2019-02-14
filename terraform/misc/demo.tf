variable "access_key" {}
variable "secret_key" {}
variable "region" {
  default = "us-east-1"
}


provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region     = "${var.region}"
}

/*
# Uncomment for remote state backend
 terraform {
  backend "s3" {
    bucket         = "fog-bigdata-terraform-backend"
    dynamodb_table = "terraform-state-lock-dynamo"
    key            = "backend/terraform.tfstate"
    region         = "${var.region}"
    encrypt = true
  }
} */

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags {
    Name = "requests-per-second-analysis-vpc"
  }
}
variable "public_subnet_cidr" {
  description = "CIDR for the public subnet"
  default = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR for the private subnet"
  default = "10.0.2.0/24"
}

variable "key_path" {
  description = "SSH Public Key path"
  default = "id_rsa.pub"
}

variable "ami" {
  description = "Amazon Linux AMI"
  default = "ami-4fffc834"
}

# Define the public subnet
resource "aws_subnet" "public-subnet" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "${var.public_subnet_cidr}"
  availability_zone = "us-east-1b"

  tags {
    Name = "Public Subnet"
  }
}

# Define the private subnet
resource "aws_subnet" "private-subnet" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "${var.private_subnet_cidr}"
  availability_zone = "us-east-1b"

  tags {
    Name = "Private Subnet"
  }
}

# Define the internet gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = "${aws_vpc.main.id}"

  tags {
    Name = "VPC IGW"
  }
}

# Define the route table
resource "aws_route_table" "web-public-rt" {
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.gw.id}"
  }

  tags {
    Name = "Public Subnet RT"
  }
}

# Assign the route table to the public Subnet
resource "aws_route_table_association" "web-public-rt" {
  subnet_id = "${aws_subnet.public-subnet.id}"
  route_table_id = "${aws_route_table.web-public-rt.id}"
}

# Define the security group for public subnet
resource "aws_security_group" "sgweb" {
  name = "vpc_test_web"
  description = "Allow incoming HTTP connections & SSH access"

  # Allow all egress traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }


  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = -1
    to_port = -1
    protocol = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks =  ["0.0.0.0/0"]
  }

  vpc_id="${aws_vpc.main.id}"

  tags {
    Name = "Web Server SG"
  }
}

# Define the security group for private subnet
resource "aws_security_group" "sgdb"{
  name = "sg_test_web"
  description = "Allow traffic from public subnet"

  ingress {
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    cidr_blocks = ["${var.public_subnet_cidr}"]
  }

  ingress {
    from_port = -1
    to_port = -1
    protocol = "icmp"
    cidr_blocks = ["${var.public_subnet_cidr}"]
  }

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["${var.public_subnet_cidr}"]
  }

  vpc_id = "${aws_vpc.main.id}"

  tags {
    Name = "DB SG"
  }
}

# Define SSH key pair for our instances
resource "aws_key_pair" "default" {
  key_name = "vpctestkeypair"
  public_key = "${file("${var.key_path}")}"
}

# Define webserver inside the public subnet
resource "aws_instance" "wb" {
   ami  = "${var.ami}"
   instance_type = "t1.micro"
   key_name = "${aws_key_pair.default.id}"
   subnet_id = "${aws_subnet.public-subnet.id}"
   vpc_security_group_ids = ["${aws_security_group.sgweb.id}"]
   associate_public_ip_address = true
   source_dest_check = false
   user_data = "${file("install.sh")}"

  tags {
    Name = "webserver"
  }



}


# Define database inside the private subnet
resource "aws_instance" "db" {
   ami  = "${var.ami}"
   instance_type = "t1.micro"
   key_name = "${aws_key_pair.default.id}"
   subnet_id = "${aws_subnet.private-subnet.id}"
   vpc_security_group_ids = ["${aws_security_group.sgdb.id}"]
   source_dest_check = false

  tags {
    Name = "database"
  }
}

output "db-ip" {
  value = "${aws_instance.db.private_ip}"
}

output "webserver-ip" {
  value = "${aws_instance.wb.public_ip}"
}



############################## FLOWLOG ##############################

// Create flowlog from our main VPC to a cloudwatch stream
resource "aws_flow_log" "flowlog-cw" {
  iam_role_arn    = "${aws_iam_role.cw-full-access-role.arn}"
  log_destination = "${aws_cloudwatch_log_group.rps-cloudwatch-log-group.arn}"
  traffic_type    = "ALL"
  vpc_id          = "${aws_vpc.main.id}"
}

// Create cloudwatch log group
resource "aws_cloudwatch_log_group" "rps-cloudwatch-log-group" {}

// Role to provide our flowlog with full access to cloud watch
resource "aws_iam_role" "cw-full-access-role" {

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}
data "aws_iam_policy" "CloudWatchFullAccess" {
  arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

resource "aws_iam_role_policy_attachment" "cw-full-access-to-role" {
  role = "${aws_iam_role.cw-full-access-role.name}"
  policy_arn = "${data.aws_iam_policy.CloudWatchFullAccess.arn}"
}



resource "aws_flow_log" "flowlog-s3" {
  log_destination = "${aws_s3_bucket.flowlog-bucket.arn}"
  log_destination_type = "s3"
  traffic_type    = "ALL"
  vpc_id          = "${aws_vpc.main.id}"
}
resource "aws_s3_bucket" "flowlog-bucket" {
  bucket = "rps-flowlog-bucket"

}




### KINESIS STREAM ###

// Kinesis stream reading from the flowlog's events
resource "aws_kinesis_stream" "kinesis-flowlog-stream" {
  name             = "kinesis-flowlog-stream"
  shard_count      = 1
  retention_period = 24

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
  ]
}

// Filter subscribed to the cloudwatch flowlog stream
resource "aws_cloudwatch_log_subscription_filter" "cloudwatch-to-kinesis-subscription" {
  name = "test_lambdafunction_logfilter"

  role_arn        = "${aws_iam_role.full-access-to-kinesis.arn}"
  log_group_name  = "${aws_cloudwatch_log_group.rps-cloudwatch-log-group.name}"
  filter_pattern  = ""
  destination_arn = "${aws_kinesis_stream.kinesis-flowlog-stream.arn}"
}

resource "aws_iam_role" "full-access-to-kinesis" {
  name = "cwlog-to-kinesis-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "logs.${var.region}.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}
data "aws_iam_policy" "AmazonKinesisFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonKinesisFullAccess"
}
resource "aws_iam_role_policy_attachment" "full-access-to-kinesis-attachment" {
  role = "${aws_iam_role.full-access-to-kinesis.name}"
  policy_arn = "${data.aws_iam_policy.AmazonKinesisFullAccess.arn}"
}








/* #### Lambda stuff
locals {
  flowlog_parsing_lambda_zip_path = "${path.module}/../lambdas/flowlog-parsing-lambda/flowlog-parsing-lambda.zip"
}

resource "aws_lambda_function" "lambda_processor" {
  role          = "${aws_iam_role.lambda_iam.arn}"
  handler       = "flowlog-parsing-lambda.handler"
  runtime       = "python2.7"
  filename      = "${local.flowlog_parsing_lambda_zip_path}"
  function_name = "rpsFlowlogParser"

  environment {
    variables = {
      DELIVERY_STREAM_NAME = "${aws_cloudwatch_log_group.rps-cloudwatch-log-group.name}"
    }
  }
} */
