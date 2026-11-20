data "aws_iam_policy_document" "scheduler_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.name}-billing-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_trust.json
}

resource "aws_iam_role_policy" "run_task" {
  name = "${var.name}-run-billing-task"
  role = aws_iam_role.scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = [var.task_definition_arn]
        Condition = {
          ArnEquals = { "ecs:cluster" = var.cluster_arn }
        }
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = [var.task_execution_role_arn, var.task_role_arn]
        Condition = {
          StringLike = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" }
        }
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "billing" {
  name                = "${var.name}-due-subscription-billing"
  description         = "Runs the application's idempotent due-subscription billing job."
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "billing" {
  rule      = aws_cloudwatch_event_rule.billing.name
  target_id = "run-due-subscription-billing"
  arn       = var.cluster_arn
  role_arn  = aws_iam_role.scheduler.arn
  input = jsonencode({
    containerOverrides = [{
      name    = "api"
      command = ["python", "-m", "app.run_billing"]
    }]
  })
  ecs_target {
    task_count          = 1
    task_definition_arn = var.task_definition_arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"
    network_configuration {
      subnets          = var.private_subnet_ids
      security_groups  = [var.task_security_group_id]
      assign_public_ip = false
    }
  }
}
