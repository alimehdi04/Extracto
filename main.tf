provider "aws" {
  region = "ap-south-1" 
}

variable "gemini_api_key" {
  type      = string
  sensitive = true
}

# 1. The S3 Bucket (For Document Uploads)
resource "aws_s3_bucket" "extracto_docs" {
  bucket = "extracto-docs-alimehdi-2026" 
}

# 2. The DynamoDB Table (For AI Results - Strictly Free Tier)
resource "aws_dynamodb_table" "extracto_results" {
  name           = "ExtractoResults"
  billing_mode   = "PROVISIONED"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "document_id"

  attribute {
    name = "document_id"
    type = "S"
  }
}

# 3. IAM Role (Grants Lambda permission to run)
resource "aws_iam_role" "lambda_exec_role" {
  name = "extracto_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# 4. IAM Policy (Grants Lambda permission to read S3 and write to DynamoDB)
resource "aws_iam_role_policy" "lambda_policy" {
  name = "extracto_lambda_policy"
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.extracto_docs.arn}/*"
      },
      {
        Effect = "Allow"
        Action = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.extracto_results.arn
      }
    ]
  })
}

# 5. Package the Python Code Automatically
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/lambda_function.zip"
}

# 6. The Lambda Function
resource "aws_lambda_function" "extracto_analyzer" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "ExtractoAnalyzer"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  memory_size      = 256
  timeout          = 30

  # ADD THIS BLOCK:
  environment {
    variables = {
      GEMINI_API_KEY = var.gemini_api_key
    }
  }
}

# 7. S3 Event Trigger (Connects S3 to Lambda)
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.extracto_analyzer.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.extracto_docs.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.extracto_docs.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.extracto_analyzer.arn
    events              = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_lambda_permission.allow_s3]
}