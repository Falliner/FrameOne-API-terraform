output "bucket_name" {
  value = aws_s3_bucket.replays.bucket
}

output "lambda_function" {
  value = aws_lambda_function.uploader.function_name
}

output "dynamodb_table" {
  value = aws_dynamodb_table.uploads.name
}