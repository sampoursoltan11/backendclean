# ============================================================================
# IAM Module - Outputs
# ============================================================================

output "deployment_user_name" {
  description = "IAM user name for deployment"
  value       = aws_iam_user.deployment.name
}

output "deployment_user_arn" {
  description = "IAM user ARN for deployment"
  value       = aws_iam_user.deployment.arn
}

output "access_key_id" {
  description = "IAM access key ID (if created)"
  value       = var.create_access_key ? aws_iam_access_key.deployment[0].id : ""
  sensitive   = true
}

output "secret_access_key" {
  description = "IAM secret access key (if created)"
  value       = var.create_access_key ? aws_iam_access_key.deployment[0].secret : ""
  sensitive   = true
}
