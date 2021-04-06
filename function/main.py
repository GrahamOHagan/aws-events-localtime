import boto3
import datetime
import logging
import os
import pytz

events = boto3.client('events')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOGGLE = os.environ.get("TOGGLE", "LocalTime")


def lambda_handler(event=None, Contect=None):
    main(event["detail"])


def main(event):
    # Find arn of resource from EventBridge event
    if event["eventName"] == "PutRule":
        arn = event["responseElements"]["ruleArn"]
    else:
        arn = event["requestParameters"]["resourceARN"]

    # Skip if resource does not have a tag with TOGGLE key
    response = events.list_tags_for_resource(ResourceARN=arn)
    timezone = [tag["Value"] for tag in response["Tags"] if tag["Key"] == TOGGLE]
    if not timezone:
        logger.info(f"Resource {arn} does not have {TOGGLE} tagged so will be ignored.")
        return

    # Skip if timezone (TOGGLE keys value) is invalid
    timezone = timezone[0]
    if timezone not in list(pytz.common_timezones):
        logger.error(f"{timezone} is not a valid time zone. Please check pytz documentation.")
        return

    name = arn.split("rule/")[1]

    logger.info(f"EventBridge Rule Arn: {arn}")
    logger.info(f"Rule Name: {name}")
    logger.info(f"Rule Time Zone: {timezone}")

    # Get rule details
    response = events.describe_rule(
        Name=name,
        EventBusName='default'
    )

    expression = response["ScheduleExpression"]
    description = response["Description"]
    role_arn = response.get("RoleArn", None)

    logger.info(f"Rule Cron Expression: {expression}")

    # Calculate new expression
    new_expression = calculate_expression(timezone, expression)

    if expression != new_expression:
        """
        Applying terraform overrides the adjusted expression so this should just
        adjust it back. Performing TagResource manually may result in the hour
        dropping by 1 every time.
        """
        logger.info(f"New expression: {new_expression}")
        if role_arn:
            response = events.put_rule(
                Name=name,
                ScheduleExpression=new_expression,
                Description=description,
                RoleArn=role_arn
            )
        else:
            response = events.put_rule(
                Name=name,
                ScheduleExpression=new_expression,
                Description=description
            )
        return

    logger.info(f"Current expression: {expression}")


def calculate_expression(tz, exp):
    """Workout new Cron expression based on timezone."""
    utc = pytz.timezone('UTC')
    now = utc.localize(datetime.datetime.utcnow())
    local_time = now.astimezone(pytz.timezone(tz))

    if local_time.tzinfo._dst.seconds != 0:
        logger.info("Daylight savings in effect.")
        split_exp = exp.split(" ")
        split_exp[1] = format_hour(split_exp[1])
        return " ".join(split_exp)
    else:
        logger.info("Daylight savings not in effect.")
        return exp


def format_hour(string):
    """Format the hour component of the expression."""
    if "," in string:
        # Comma separated values
        hours = string.split(",")
        hours = [subtract_hour(h) for h in hours]
        return ",".join(hours)
    elif "-" in string:
        # Range of values
        hours = string.split("-")
        hours = [subtract_hour(h) for h in hours]
        return "-".join(hours)
    else:
        # Single value
        return subtract_hour(string)


def subtract_hour(string):
    """Subtracts an hour from the string - 24 hour format."""
    if string == "0":
        return "23"
    hour = int(string)
    return str(hour - 1)
