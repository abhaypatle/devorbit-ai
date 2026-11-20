resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.name}-db" }
}

resource "aws_db_instance" "this" {
  identifier                            = "${var.name}-postgres"
  engine                                = "postgres"
  engine_version                        = var.engine_version
  instance_class                        = var.instance_class
  allocated_storage                     = var.allocated_storage_gb
  max_allocated_storage                 = var.allocated_storage_gb * 2
  storage_encrypted                     = true
  db_name                               = "devorbit"
  username                              = "devorbit_admin"
  manage_master_user_password           = true
  db_subnet_group_name                  = aws_db_subnet_group.this.name
  vpc_security_group_ids                = [var.database_security_group_id]
  publicly_accessible                   = false
  multi_az                              = true
  backup_retention_period               = var.backup_retention_days
  copy_tags_to_snapshot                 = true
  auto_minor_version_upgrade            = true
  deletion_protection                   = var.deletion_protection
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  apply_immediately                     = false
  skip_final_snapshot                   = false
  final_snapshot_identifier             = "${var.name}-final-snapshot"
  tags                                  = { Name = "${var.name}-postgres" }
}
