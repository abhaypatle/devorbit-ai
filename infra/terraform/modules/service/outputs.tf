output "api_base_url" {
  value = "${var.certificate_arn == "" ? "http" : "https"}://${aws_lb.api.dns_name}"
}
output "cluster_arn" { value = aws_ecs_cluster.this.arn }
output "cluster_name" { value = aws_ecs_cluster.this.name }
output "task_definition_arn" { value = aws_ecs_task_definition.api.arn }
output "execution_role_arn" { value = aws_iam_role.execution.arn }
output "task_role_arn" { value = aws_iam_role.task.arn }
output "log_group_name" { value = aws_cloudwatch_log_group.api.name }
output "load_balancer_arn_suffix" { value = aws_lb.api.arn_suffix }
output "target_group_arn_suffix" { value = aws_lb_target_group.api.arn_suffix }
