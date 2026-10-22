output "postgres_endpoint" {
  value = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "application_url" {
  value = "http://${aws_lb.main.dns_name}"
}
