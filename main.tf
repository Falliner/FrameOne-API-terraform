terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── S3 Bucket ──────────────────────────────────────────────
resource "aws_s3_bucket" "replays" {
  bucket        = var.bucket_name
  force_destroy = true
}

# ── DynamoDB Table ─────────────────────────────────────────
resource "aws_dynamodb_table" "uploads" {
  name         = "frameone-uploads"
  billing_mode = "PAY_PER_REQUEST"  # free tier friendly
  hash_key     = "replay_key"

  attribute {
    name = "replay_key"
    type = "S"
  }
}

# ── IAM Role for Lambda ────────────────────────────────────
resource "aws_iam_role" "lambda_role" {
  name = "frameone-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.replays.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.uploads.arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ── Lambda Function ────────────────────────────────────────
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "uploader" {
  function_name    = "frameone-uploader"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      API_URL        = var.api_url
      DYNAMODB_TABLE = aws_dynamodb_table.uploads.name
    }
  }
}

# ── S3 → Lambda Trigger ────────────────────────────────────
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.replays.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.uploader.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.uploader.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.replays.arn
}