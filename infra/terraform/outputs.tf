output "api_base_url" {
  description = "Backend API base URL."
  value       = module.service.api_base_url
}

output "documents_bucket_name" {
  description = "Private S3 bucket for project documents and invoice PDFs."
  value       = module.storage.bucket_name
}

output "runtime_secret_arn" {
  description = "Secrets Manager secret ARN containing application keys."
  value       = module.storage.runtime_secret_arn
}

output "database_endpoint" {
  description = "Private RDS endpoint; credentials are managed by Secrets Manager."
  value       = module.database.address
}

output "ecs_cluster_name" {
  description = "ECS cluster running the backend API and scheduled billing task."
  value       = module.service.cluster_name
}
