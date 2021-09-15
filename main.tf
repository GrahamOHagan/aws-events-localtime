# Lambda Function
resource "aws_lambda_function" "this" {
  filename      = local.zip_location
  function_name = local.lambda_name
  role          = aws_iam_role.this.arn
  handler       = "main.lambda_handler"

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  runtime = "python3.7"
  timeout = 300

  environment {
    variables = {
      TOGGLE = var.trigger_tag
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = var.tags
}

# Lambda Role
resource "aws_iam_role" "this" {
  name = "${local.lambda_name}-role"

  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json

  inline_policy {
    name = "lambda-policy"

    policy = data.aws_iam_policy_document.lambda_policy.json
  }

  tags = var.tags
}

# Eventbridge event rules for Winter and Summer
resource "aws_cloudwatch_event_rule" "summer" {
  name = "daylight-savings-summer-event"
  description = "Trigger localtime lambda in summer - ${var.summer_expression}"
  schedule_expression = var.summer_expression

  tags = var.tags
}
resource "aws_cloudwatch_event_target" "summer" {
  rule      = aws_cloudwatch_event_rule.summer.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_cloudwatch_event_rule" "winter" {
  name = "daylight-savings-winter-event"
  description = "Trigger localtime lambda in winter - ${var.winter_expression}"
  schedule_expression = var.winter_expression

  tags = var.tags
}
resource "aws_cloudwatch_event_target" "winter" {
  rule      = aws_cloudwatch_event_rule.winter.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.this.arn
}

# Eventbridge pattern rule - When a rule is updated
resource "aws_cloudwatch_event_rule" "this" {
  name = "rule-creation-event"
  description = "Trigger localtime lambda when a rule is created or updated and has the ${var.trigger_tag} tag."
  event_pattern = <<EOF
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "source": [
    "aws.events"
  ],
  "detail": {
    "eventName": [
      "PutRule",
      "TagResource",
      "TagResources"
    ],
    "eventSource": [
      "events.amazonaws.com"
    ],
    "userIdentity": {
      "arn": [{ "anything-but": "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/${local.lambda_name}-role/${local.lambda_name}" }]
    }
  }
}
EOF

  tags = var.tags
}
resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.this.arn
}

# Lambda invoke permissions
resource "aws_lambda_permission" "allow_summer_trigger" {
  statement_id  = "AllowExecutionFromCWSummerEvent"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.this.arn
  source_arn    = aws_cloudwatch_event_rule.summer.arn
}

resource "aws_lambda_permission" "allow_winter_trigger" {
  statement_id  = "AllowExecutionFromCWWinterEvent"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.this.arn
  source_arn    = aws_cloudwatch_event_rule.winter.arn
}

resource "aws_lambda_permission" "allow_event_trigger" {
  statement_id  = "AllowExecutionFromCWEvent"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.this.arn
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
