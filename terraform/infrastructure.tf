variable "access_key" {}
variable "secret_key" {}
variable "account_id" {}
variable "region" {
  default = "us-east-1"
}


provider "aws" {
  version = "~> 1.58"
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

resource "aws_instance" "stream_data_mock_instance" {
  instance_type = "t2.micro"
  ami = "ami-035be7bafff33b6b6"
  iam_instance_profile= "EC2_S3Access"
  key_name= "${aws_key_pair.default-vpc-access.key_name}"
  provisioner "local-exec" {// todo add ip to hosts
    command = "rm ansible-hosts.ini && echo \"${self.public_ip} ansible_user=ec2-user\" >> ansible-hosts.ini && ansible-playbook ec2-provisioning.yml --private-key ~/Downloads/default-vpc-access.pem -i ansible-hosts.ini"
  }

}
output "public_ip" {
  value = "${aws_instance.stream_data_mock_instance.public_ip}"
}

resource "aws_key_pair" "default-vpc-access" {
  key_name   = "default-vpc-access"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBvRU73Kgr7rxTgXNOiDZG4/iYubUy1P4GsSE4fZlcs3TIDm5NltGFXo4MDwXSvBJuds1zWSDrNpnOTtWfifpenCZs/+y4TeBygK/5Pt04xQyboO5ytawSgLm4VCFwj8nibAcO1wkAtjh5+Q+sVcnsIhW7qTJ5OJwdTYJg4JJNJKn4FIfBMnucZkge2687qLioN3tPwgYG9LsPkdZHEM5kd/dO2AkFkzA3knREVmXCnpyq/c1gy9ufecMeR4nPszvHMgRlzfxx9SuDqjXER7KqYQRmmy7c7ThtwZ33BUVfRwnT+4jUns9WcShGYG3uWgItU9XWytX4JCGxtP0pXEUH dafault-vpc-access"
}
output "default-vpc-access-public_key" {
  value = "${aws_key_pair.default-vpc-access.public_key}"
}



resource "aws_s3_bucket" "fog-datasets" {
  acl = ""
  force_destroy = ""
}

/* Publish streamed data to an aws sns topic */
resource "aws_sns_topic" "bmw-data-upload" {
  name = "bmw-data-upload"
  display_name = "BMW push"
  policy = <<POLICY
{
  "Version": "2008-10-17",
  "Id": "__default_policy_ID",
  "Statement": [
    {
      "Sid": "__default_statement_ID",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": [
        "SNS:GetTopicAttributes",
        "SNS:SetTopicAttributes",
        "SNS:AddPermission",
        "SNS:RemovePermission",
        "SNS:DeleteTopic",
        "SNS:Subscribe",
        "SNS:ListSubscriptionsByTopic",
        "SNS:Publish",
        "SNS:Receive"
      ],
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:bmw-data-upload",
      "Condition": {
        "StringEquals": {
          "AWS:SourceOwner": "${var.account_id}"
        }
      }
    },
    {
      "Sid": "_s3",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:bmw-data-upload",
      "Condition": {
        "ArnLike":{"aws:SourceArn": "${aws_s3_bucket.fog-datasets.arn}"}
      }
    },
    {
      "Sid": "_s3s",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:bmw-data-upload",
      "Condition": {
        "StringEquals": {
          "aws:SourceArn": "arn:aws:s3:::fog-bigdata-bmw-data"
        }
      }
    }
  ]
}
POLICY
}

resource "aws_s3_bucket_notification" "StreamMockCreate" {
  bucket = "${aws_s3_bucket.fog-datasets.id}"


  topic {
    topic_arn     = "${aws_sns_topic.bmw-data-upload.arn}"
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "streaming-data-mock"
  }
}

