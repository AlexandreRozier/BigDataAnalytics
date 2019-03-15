variable "access_key" {}
variable "secret_key" {}

variable "account_id" {
  description = "AWS Account id"
}

variable "region" {
  default = "us-east-1"
}

variable "bmw-bucket" {
  description = "Name of the bucket containing the BMW data"
}

provider "aws" {
  version    = "~> 1.58"
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

resource "aws_security_group" "default" {
  name        = "allow_ssh"
  description = "Allow SSH inbound traffic"

  // Needed for SSH access
  ingress {
    from_port   = 0
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  // Allow every outgoing traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "stream_data_mock_instance" {
  instance_type        = "t2.micro"
  security_groups      = ["${aws_security_group.default.name}"]
  ami                  = "ami-035be7bafff33b6b6"
  iam_instance_profile = "EC2_S3Access"
  key_name             = "${aws_key_pair.default-vpc-access.key_name}"

  depends_on =["aws_s3_bucket.datasets"]
  provisioner "local-exec" {
    command = <<EOF
  export ANSIBLE_HOST_KEY_CHECKING=False; 
  rm ansible-hosts.ini; 
  echo "${self.public_ip} ansible_user=ec2-user" >> ansible-hosts.ini ; 
  sleep 10; 
  ansible-playbook ec2-provisioning.yml --private-key ~/Downloads/default-vpc-access.pem -i ansible-hosts.ini --extra-vars "S3_BUCKET_NAME=${aws_s3_bucket.datasets.bucket} S3_KEY=streaming-data-mock.csv S3_OUTPUT_BUCKET=${aws_s3_bucket.datasets.bucket}  S3_OUTPUT_DIRECTORY=streaming-data-mock";
  EOF
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

resource "aws_s3_bucket" "datasets" {
  acl           = ""
  force_destroy = true                 // dangerous, for dev purpose
  bucket        = "sanitized-datasets"
  

  provisioner "local-exec" {
    command = "aws s3 cp ../mock_data/streaming-data-mock.csv s3://${self.bucket}/streaming-data-mock.csv"
  }

  // Preprocess data to shape it according to our models needs
  provisioner "local-exec" {
    command = "python ../models/deep_ar/data_preprocessing.py"

    environment {
      BMW_DATA_BUCKET       = "${var.bmw-bucket}"
      SANITIZED_DATA_BUCKET = "${self.bucket}"
      DATA_FREQUENCY        = "${var.data_aggregation_frequency}"
    }
  }


  // Train a Mean Predictor & a DeepAR model and export them as endpoint.
  // Both models are trained in parallel thanks to the '&', to speed up the provisioning.
  // WARING: takes ~ 2 hours
  provisioner "local-exec" {
    command = <<EOF
python ../models/mean_predictor/train_deploy.py --trainpath s3://${aws_s3_bucket.datasets.bucket}/rcf/data/train/data.csv --role ${aws_iam_role.sm_role.arn} --freq ${var.data_aggregation_frequency} &
python ../models/deep_ar/train_deploy.py &
wait
EOF

    environment {
      BMW_DATA_BUCKET       = "fog-bigdata-bmw-data"
      SANITIZED_DATA_BUCKET = "${self.bucket}"
      SAGEMAKER_ROLE_ARN    = "${aws_iam_role.sm_role.arn}"
      ENDPOINT_NAME         = "${var.deepar_endpoint_name}"
      DATA_FREQUENCY        = "${var.data_aggregation_frequency}"
    }
  }

  // Delete endpoints on destroy
  provisioner "local-exec" {
    when = "destroy"
    command = "aws sagemaker delete-endpoint --endpoint-name ${var.mp_endpoint_name}"
    on_failure = "continue"
  }

  provisioner "local-exec" {
    when = "destroy"
    command = "aws sagemaker delete-endpoint --endpoint-name ${var.deepar_endpoint_name}"
    on_failure = "continue"
  }

}

/* Publish streamed data to an aws sns topic */
resource "aws_sns_topic" "data-upload" {
  name         = "data-upload"
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
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:data-upload",
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
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:data-upload",
      "Condition": {
        "ArnLike":{"aws:SourceArn": "${aws_s3_bucket.datasets.arn}"}
      }
    },
    {
      "Sid": "_s3s",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:${var.region}:${var.account_id}:data-upload",
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
  bucket = "${aws_s3_bucket.datasets.id}"

  topic {
    topic_arn     = "${aws_sns_topic.data-upload.arn}"
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "streaming-data-mock"
  }
}

resource "aws_iam_role" "sm_role" {
  description = "Role giving Sagemaker services access to ECS, SM, S3 and EC2 Container"
  name = "sage_maker"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecsfa-to-sm" {
  role       = "${aws_iam_role.sm_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_role_policy_attachment" "ec2fa-to-sm" {
  role       = "${aws_iam_role.sm_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
}

resource "aws_iam_role_policy_attachment" "smfa-to-sm" {
  role       = "${aws_iam_role.sm_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3fa-to-sm" {
  role       = "${aws_iam_role.sm_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
