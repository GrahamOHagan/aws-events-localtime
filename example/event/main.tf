resource "aws_cloudwatch_event_rule" "test" {
  name = "test-event"
  description = "Test if the creation of this triggers another rule."
  schedule_expression = "cron(0 0-5 ? 3 * *)"

  tags = {
    Name        = "TestingLocalTimeService"
    Role        = "TestingLocalTimeService"
    LocalTime   = "Europe/London"
    Environment = "Development"
  }
}
