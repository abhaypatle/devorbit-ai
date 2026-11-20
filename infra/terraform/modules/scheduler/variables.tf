variable "name" { type = string }
variable "schedule_expression" { type = string }
variable "cluster_arn" { type = string }
variable "task_definition_arn" { type = string }
variable "task_execution_role_arn" { type = string }
variable "task_role_arn" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "task_security_group_id" { type = string }
