resource "aws_s3_bucket" "documents" {
  bucket = "${var.name}-documents-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${var.name}-documents" }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_secretsmanager_secret" "runtime" {
  name                    = "${var.name}/runtime"
  description             = "Runtime application secrets for DevOrbit AI."
  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "runtime" {
  secret_id     = aws_secretsmanager_secret.runtime.id
  secret_string = var.runtime_secret_json
}
