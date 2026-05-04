import boto3
import requests
import os
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    api_url = os.environ["API_URL"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        #Download replay file from S3
        file_obj = s3.get_object(Bucket=bucket, Key=key)
        file_data = file_obj["Body"].read()

        try:
            #Step 1: GET the presigned POST url + fields
            presign_response = requests.get(api_url)
            presign_data = presign_response.json()

            upload_url = presign_data["result"]
            fields     = presign_data["fields"]  #dict of required form fields

            #Step 2: POST the file to the presigned S3 URL
            response = requests.post(
                upload_url,
                data=fields,
                files={"file": (key, file_data, "application/zip")}
            )
            status = "success" if response.status_code in [200, 204] else "failed"
            detail = response.text

        except Exception as e:
            status = "error"
            detail = str(e)

        #Log to DynamoDB
        table.put_item(Item={
            "replay_key": key,
            "timestamp":  datetime.utcnow().isoformat(),
            "status":     status,
            "detail":     detail[:500]
        })
        print(f"{key} → {status}")