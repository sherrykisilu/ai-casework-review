variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "name" {
  type    = string
  default = "ai-casework-review"
}

variable "api_image" {
  type        = string
  description = "Immutable API/worker container image URI."
}

variable "web_image" {
  type        = string
  description = "Immutable web container image URI."
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL password supplied through a secure CI secret or secrets manager."
}

variable "django_secret_key" {
  type        = string
  sensitive   = true
  description = "Django signing key supplied through a secure CI secret."
}

variable "monthly_case_limit" {
  type    = number
  default = 3000
}
