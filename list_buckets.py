#!/usr/bin/env python3

import os

import boto3
from dotenv import load_dotenv  

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:9002"),
    aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "admin"),
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
)

for bucket in s3.list_buckets()["Buckets"]:
    print(bucket["Name"])
