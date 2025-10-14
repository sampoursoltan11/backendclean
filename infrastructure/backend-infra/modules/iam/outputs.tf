# IAM Module Outputs

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "backend_service_role_arn" {
  description = "ARN of the backend service role"
  value       = aws_iam_role.backend_service.arn
}

output "backend_service_role_name" {
  description = "Name of the backend service role"
  value       = aws_iam_role.backend_service.name
}
