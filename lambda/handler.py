import boto3
import requests
import os
from datetime import datetime
from time import sleep

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

MAX_RETRIES = 3
RETRY_DELAY = 2  #seconds between retries

def upload_with_retry(api_url, key, file_data):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            #Step 1: GET presigned URL
            presign_response = requests.get(api_url, timeout=10)
            presign_response.raise_for_status()
            presign_data = presign_response.json()

            upload_url = presign_data["result"]
            fields     = presign_data["fields"]

            #Step 2: POST file to presigned URL
            response = requests.post(
                upload_url,
                data=fields,
                files={"file": (key, file_data, "application/zip")},
                timeout=30
            )

            if response.status_code in [200, 204]:
                return "success", f"Uploaded on attempt {attempt}"

            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            print(f"Attempt {attempt} failed: {last_error}")

        except requests.exceptions.Timeout:
            last_error = f"Attempt {attempt} timed out"
            print(last_error)
        except requests.exceptions.RequestException as e:
            last_error = f"Attempt {attempt} request error: {str(e)}"
            print(last_error)
        except KeyError as e:
            #API response missing expected fields - no point retrying
            return "error", f"Unexpected API response, missing key: {str(e)}"

        if attempt < MAX_RETRIES:
            sleep(RETRY_DELAY)

    return "failed", last_error

def lambda_handler(event, context):
    table   = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    api_url = os.environ["API_URL"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        try:
            file_obj  = s3.get_object(Bucket=bucket, Key=key)
            file_data = file_obj["Body"].read()
        except Exception as e:
            print(f"Failed to read {key} from S3: {e}")
            table.put_item(Item={
                "replay_key": key,
                "timestamp":  datetime.utcnow().isoformat(),
                "status":     "error",
                "detail":     f"S3 read failed: {str(e)[:500]}"
            })
            continue

        status, detail = upload_with_retry(api_url, key, file_data)

        table.put_item(Item={
            "replay_key": key,
            "timestamp":  datetime.utcnow().isoformat(),
            "status":     status,
            "detail":     detail[:500]
        })
        print(f"{key} → {status}: {detail}")