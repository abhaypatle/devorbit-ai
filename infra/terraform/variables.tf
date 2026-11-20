variable "aws_region" {
  description = "AWS deployment region."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short lowercase application name used in resource names."
  type        = string
  default     = "devorbit"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "IPv4 CIDR range for the application VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of availability zones for public and private subnets."
  type        = number
  default     = 2
  validation {
    condition     = var.availability_zone_count >= 2 && var.availability_zone_count <= 3
    error_message = "Use between two and three availability zones."
  }
}

variable "backend_image" {
  description = "Immutable backend container image URI, normally an ECR image pinned by digest."
  type        = string
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.t4g.small"
}

variable "db_engine_version" {
  description = "Supported RDS PostgreSQL 16 minor version in the selected region."
  type        = string
  default     = "16.4"
}

variable "db_allocated_storage_gb" {
  description = "Initial encrypted RDS storage in GiB."
  type        = number
  default     = 50
}

variable "db_backup_retention_days" {
  description = "Automated RDS backup retention."
  type        = number
  default     = 14
}

variable "db_deletion_protection" {
  description = "Protect the database from accidental deletion."
  type        = bool
  default     = true
}

variable "api_allowed_cidrs" {
  description = "CIDR ranges allowed to reach the ALB. Restrict this for private agency deployments."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alb_certificate_arn" {
  description = "Optional ACM certificate ARN; when set, HTTP redirects to HTTPS."
  type        = string
  default     = ""
}

variable "runtime_secret_json" {
  description = "JSON for Secrets Manager with JWT_SECRET_KEY, PAYMENT_WEBHOOK_SECRET and optional OPENAI_API_KEY. Protect Terraform state."
  type        = string
  sensitive   = true
  validation {
    condition     = can(jsondecode(var.runtime_secret_json).JWT_SECRET_KEY) && length(jsondecode(var.runtime_secret_json).JWT_SECRET_KEY) >= 32
    error_message = "runtime_secret_json must contain a JWT_SECRET_KEY of at least 32 characters."
  }
}

variable "cors_origins" {
  description = "Allowed browser origins for direct API access; same-origin proxy deployments can use the frontend URL."
  type        = list(string)
  default     = ["https://app.example.com"]
}

variable "billing_schedule_expression" {
  description = "EventBridge schedule expression for daily due-subscription billing."
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "alarm_notification_email" {
  description = "Optional email address for CloudWatch alarm notifications."
  type        = string
  default     = ""
}
