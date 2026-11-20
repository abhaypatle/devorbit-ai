locals {
  name = "${var.project_name}-${var.environment}"
}

module "network" {
  source = "./modules/network"

  name               = local.name
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zone_count
  api_allowed_cidrs  = var.api_allowed_cidrs
}

module "storage" {
  source = "./modules/storage"

  name                = local.name
  runtime_secret_json = var.runtime_secret_json
}

module "database" {
  source = "./modules/database"

  name                       = local.name
  vpc_id                     = module.network.vpc_id
  private_subnet_ids         = module.network.private_subnet_ids
  database_security_group_id = module.network.database_security_group_id
  engine_version             = var.db_engine_version
  instance_class             = var.db_instance_class
  allocated_storage_gb       = var.db_allocated_storage_gb
  backup_retention_days      = var.db_backup_retention_days
  deletion_protection        = var.db_deletion_protection
}

module "service" {
  source = "./modules/service"

  name                   = local.name
  aws_region             = var.aws_region
  vpc_id                 = module.network.vpc_id
  public_subnet_ids      = module.network.public_subnet_ids
  private_subnet_ids     = module.network.private_subnet_ids
  alb_security_group_id  = module.network.alb_security_group_id
  task_security_group_id = module.network.task_security_group_id
  bucket_arn             = module.storage.bucket_arn
  bucket_name            = module.storage.bucket_name
  runtime_secret_arn     = module.storage.runtime_secret_arn
  database_secret_arn    = module.database.master_secret_arn
  database_host          = module.database.address
  database_name          = module.database.database_name
  image                  = var.backend_image
  certificate_arn        = var.alb_certificate_arn
  cors_origins           = var.cors_origins
}

module "scheduler" {
  source = "./modules/scheduler"

  name                    = local.name
  schedule_expression     = var.billing_schedule_expression
  cluster_arn             = module.service.cluster_arn
  task_definition_arn     = module.service.task_definition_arn
  task_execution_role_arn = module.service.execution_role_arn
  task_role_arn           = module.service.task_role_arn
  private_subnet_ids      = module.network.private_subnet_ids
  task_security_group_id  = module.network.task_security_group_id
}

module "monitoring" {
  source = "./modules/monitoring"

  name                     = local.name
  log_group_name           = module.service.log_group_name
  alarm_notification_email = var.alarm_notification_email
  load_balancer_arn_suffix = module.service.load_balancer_arn_suffix
  target_group_arn_suffix  = module.service.target_group_arn_suffix
}
