# DynamoDB Module Outputs

output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.tra_system.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.tra_system.arn
}

output "table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.tra_system.id
}

output "table_stream_arn" {
  description = "ARN of the table stream"
  value       = aws_dynamodb_table.tra_system.stream_arn
}

output "gsi_names" {
  description = "List of Global Secondary Index names"
  value = [
    "gsi2-session-entity",
    "gsi3-assessment-events",
    "gsi4-state-updated",
    "gsi5-title-search",
    "gsi6-entity-type"
  ]
}
