module "service" {
  source = "../../"

  disable_put_events = true

  tags = {
    Name        = "TestingLocalTimeService"
    Role        = "TestingLocalTimeService"
    Environment = "Development"
  }
}
