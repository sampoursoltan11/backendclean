# CloudWatch Module Outputs

output "application_log_group_name" {
  description = "Name of the application log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "application_log_group_arn" {
  description = "ARN of the application log group"
  value       = aws_cloudwatch_log_group.application.arn
}

output "ecs_log_group_name" {
  description = "Name of the ECS log group"
  value       = aws_cloudwatch_log_group.ecs.name
}
