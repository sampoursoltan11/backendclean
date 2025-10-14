# ECS Module - Optional (for containerized FastAPI deployment)
# Creates ECS cluster, task definition, and service

resource "aws_ecs_cluster" "main" {
  name = var.cluster_name
  tags = var.tags
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.cluster_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([{
    name  = "tra-backend"
    image = var.container_image
    portMappings = [{ containerPort = var.container_port }]
    environment = [for k, v in var.environment_variables : { name = k, value = v }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/aws/ecs/${var.cluster_name}"
        "awslogs-region"        = "ap-southeast-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# Placeholder outputs
output "cluster_name" { value = aws_ecs_cluster.main.name }
output "cluster_arn" { value = aws_ecs_cluster.main.arn }
output "service_name" { value = "tra-backend-service" }
output "alb_dns_name" { value = "not-configured" }
