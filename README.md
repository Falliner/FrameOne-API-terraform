# FrameOne API Terraform

A Terraform project that provisions an automated replay upload pipeline on AWS, built with permission from [@ prospekt] to use the [FrameOne ACPR Replays API](https://api.frameone.net).

## What it does

Automatically uploads `.zip` replay files to the FrameOne API whenever a file is dropped into an S3 bucket. The Lambda function handles fetching a presigned URL, uploading the file, and logging the result with retry logic for failed attempts.

## AWS Resources

- **S3 bucket** — drop replay zips here to trigger the pipeline
- **Lambda function** — fetches a presigned URL from the API and uploads the file, with up to 3 retries on failure
- **DynamoDB table** — logs every upload attempt with status, detail, and timestamp
- **IAM role** — scoped permissions for Lambda to access S3, DynamoDB, and CloudWatch logs

## Prerequisites

- [Terraform](https://terraform.io) installed
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured (`aws configure`)
- AWS account (free tier is sufficient)
- Python 3 + pip

## Setup

1. Clone the repo
2. Install Lambda dependencies:
```
  pip install requests -t lambda/ --break-system-packages
```
3. Create `terraform.tfvars`:
```
   api_url     = "https://api.frameone.net/upload-zip"
   bucket_name = "your-unique-bucket-name"
```
4. Deploy:
```
   terraform init
   terraform apply
```

## Usage

Drop a `.zip` replay file into your S3 bucket:
```
aws s3 cp your-replay.zip s3://your-bucket-name/
```

Check upload logs:
```
aws dynamodb scan --table-name frameone-uploads
```

Check Lambda logs:
```
aws logs tail /aws/lambda/frameone-uploader --follow
```

## CI/CD

GitHub Actions runs `terraform validate` and `terraform plan` on every push and pull request. Required repository secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `API_URL`

## What I learned

- Provisioning AWS infrastructure with Terraform (S3, Lambda, DynamoDB, IAM)
- Event-driven architecture — S3 triggers invoking Lambda automatically
- Bundling Python dependencies into Lambda deployment packages
- Retry logic and error handling for external API calls
- CI/CD pipelines with GitHub Actions for infrastructure validation
