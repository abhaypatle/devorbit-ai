resource "aws_sns_topic" "alarms" {
  count = var.alarm_notification_email == "" ? 0 : 1
  name  = "${var.name}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_notification_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_notification_email
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.name}-alb-5xx"
  alarm_description   = "Application load balancer returned elevated 5xx responses."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_ELB_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = var.load_balancer_arn_suffix
  }
  alarm_actions = var.alarm_notification_email == "" ? [] : [aws_sns_topic.alarms[0].arn]
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_targets" {
  alarm_name          = "${var.name}-unhealthy-targets"
  alarm_description   = "One or more API targets are unhealthy."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = var.load_balancer_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }
  alarm_actions = var.alarm_notification_email == "" ? [] : [aws_sns_topic.alarms[0].arn]
}
