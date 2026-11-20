output "bucket_name" { value = aws_s3_bucket.documents.bucket }
output "bucket_arn" { value = aws_s3_bucket.documents.arn }
output "runtime_secret_arn" { value = aws_secretsmanager_secret.runtime.arn }
