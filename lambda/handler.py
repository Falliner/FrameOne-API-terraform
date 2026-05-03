import boto3
import requests
import os
import json
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    api_url = os.environ["API_URL"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        # Download the replay file from S3 into memory
        file_obj = s3.get_object(Bucket=bucket, Key=key)
        file_data = file_obj["Body"].read()

        # POST it to the API as multipart/form-data
        try:
            response = requests.post(
                api_url,
                files={"file": (key, file_data, "application/octet-stream")}
            )
            status = "success" if response.status_code == 200 else "failed"
            detail = response.text
        except Exception as e:
            status = "error"
            detail = str(e)

        # Log result to DynamoDB
        table.put_item(Item={
            "replay_key": key,
            "timestamp":  datetime.utcnow().isoformat(),
            "status":     status,
            "detail":     detail[:500]  # trim long responses
        })
        print(f"{key} → {status}")