variable "summer_expression" {
  description = "The cron expression of when to trigger lambda in the summer. Default is last Sunday of March at 01:00 UTC."
  type        = string
  default     = "cron(0 1 ? 3 1L *)"
}

variable "winter_expression" {
  description = "The cron expression of when to trigger lambda in the winter. Default is last Sunday of October at 01:00 UTC."
  type        = string
  default     = "cron(0 1 ? 10 1L *)"
}

variable "trigger_tag" {
  description = "The name of the tag key to trigger the lambda to convert the cron expression."
  type        = string
  default     = "LocalTime"
}

variable "custom_lambda_name" {
  description = "Custom name for the lambda function."
  type        = string
  default     = ""
}

variable "cloudwatch_log_retention_days" {
  description = "Retention in days for cloudwatch logs."
  type        = number
  default     = 14
}

variable "disable_put_events" {
  description = "Toggle to disable triggering the lambda for PutRule & Tag events throughout the year."
  type        = bool
  default     = false
}

variable "alarm_email_endpoint" {
  description = "Toggle Cloudwatch alarm and SNS topic email endpoint subscription."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Map of tags to apply to resources."
  type        = map(string)
  default     = {}
}

variable "lambda_runtime" {
  description = "Lambda python runtime."
  type        = string
  default     = "python3.11"
}