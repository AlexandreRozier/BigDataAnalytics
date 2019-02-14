/*variable "access_key" {}
variable "secret_key" {}

provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region     = "eu-west-1"
}


resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}


resource "aws_flow_log" "unexposed_flow_log" {
  log_destination      = "${aws_s3_bucket.unexposed_log_bucket.arn}"
  log_destination_type = "s3"
  traffic_type         = "ALL"
  vpc_id               = "${aws_vpc.main.id}"
}


  
resource "aws_s3_bucket" "unexposed_log_bucket" {
    bucket = "my-tf-test-bucket"
    acl    = "private"

    tags {
      Name        = "Unexposed Log Bucket"
      Environment = "Dev"
  }
}*/