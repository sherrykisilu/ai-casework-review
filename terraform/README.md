# AWS deployment example

This is a deliberately bounded portfolio example, not a production-ready landing zone. It shows small Fargate task definitions for the Django API, Celery worker, and React web image, plus encrypted RDS PostgreSQL and ElastiCache Redis.

The example intentionally does not apply automatically. Before real use:

- replace the default VPC and public task networking with private subnets, NAT/VPC endpoints, and an ALB;
- put `DJANGO_SECRET_KEY`, database credentials, and optional AI credentials in Secrets Manager and map them into task definitions;
- add HTTPS/ACM, WAF, centralized logs, alarms, autoscaling, image scanning, database rotation, and tested backup restoration;
- replace the example HTTP listener with HTTPS/ACM and redirect HTTP after choosing DNS boundaries;
- run migrations as a reviewed one-off ECS task before deploying a new API task definition;
- review data residency, retention, PII classification, provider terms, and human-review requirements;
- set AWS Budgets and cost alerts. Even the small RDS, Redis, NAT, logs, and Fargate resources incur ongoing cost;
- remove deletion protection only through a reviewed teardown procedure.

Run `terraform plan` with immutable image URIs and a securely supplied `db_password`. The managed data resources are protected from casual deletion.
