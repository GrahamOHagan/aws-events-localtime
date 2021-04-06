module "service" {
  source = "../../"

  tags = {
    Name        = "TestingLocalTimeService"
    Role        = "TestingLocalTimeService"
    Environment = "Development"
  }
}
