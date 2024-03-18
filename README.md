## aws-events-localtime

This module deploys a service that monitors and updates AWS EventBridge Rules (Cloudwatch Rules) that are configured with schedule expressions.

The service updates the expression after deployment from Terraform reducing the hour by 1 if daylight savings is in effect, allowing your IAC to remain as the non DST format. The rule requires a tag to toggle this service, the default being `LocalTime`, and the value set to one of pytz's timezones (e.g. "Europe/London").

For example, a rule is deployed with the expression `cron(0 12 * * ? *)` and the tag `LocalTime=Europe/London`. In summer `(after the last Sunday of March at 01:00, the clocks move forward)`, this will trigger the service to update the rule with `cron(0 11 * * ? *)`, and in winter `(after the last Sunday of October at 02:00, the clocks move back)` this will remain as per the Terraform. This will ensure that the rule is always triggered at 12:00 localtime.

The service is a lambda triggered by events matching events:PutRule API events - so Cloudtrail logging must be enabled. Additionally, twice a year the lambda is triggered and searches for all rules in the AWS account adjusting any expressions it finds.

| Variable                      | Description                                 | Default               |
| ----------------------------- |:-------------------------------------------:| ---------------------:|
| summer_expression             | When in summer to trigger the lambda        | `cron(0 1 ? 3 1L *)`  |
| winter_expression             | When in winter to trigger the lambda        | `cron(0 1 ? 10 1L *)` |
| trigger_tag                   | Name of the tag to trigger the lambda       | `LocalTime`           |
| custom_lambda_name            | Custom name for the lambda                  | `localtime-events`    |
| alarm_email_endpoint          | Toggles Alarm and email notification        | `NA`                  |
| cloudwatch_log_retention_days | Specify cloudwatch log retention in days    | `14`                  |
| disable_put_events            | Disable triggering by PutRule & Tag events  | `false`               |
| tags                          | Tags for the lambda and dependant resources | `NA`                  |
| lambda_runtime                | Lambda python runtime                       | `python3.11`          |

AWS Rules follow UTC and schedule expression format is detailed [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).
