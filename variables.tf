variable "api_url" {
  description = "The replay upload API endpoint"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "S3 bucket name for replay files (must be globally unique)"
  type        = string
  default     = "frameone-replays"
}