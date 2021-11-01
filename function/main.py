import boto3
import datetime
import logging
import os
import pytz

events = boto3.client('events')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOGGLE = os.environ.get("TOGGLE", "LocalTime")
DISABLE_PUT = os.environ.get("DISABLE_PUT", "false")


def lambda_handler(event=None, context=None):
    if event["detail-type"] == "Scheduled Event":
        # Scheduled
        logger.info("Searching for all rules in account.")
        main_wrapper()
    else:
        if DISABLE_PUT == "true":
            return
        # Newly created or updated rule.
        user = event["detail"]["userIdentity"]["arn"]
        if f"{context.function_name}-role" in user:
            logger.info("Triggered by self - Ignoring event.")
            return
        if event["detail"]["eventName"] == "PutRule":
            main(event["detail"]["responseElements"]["ruleArn"])
        else:
            main(event["detail"]["requestParameters"]["resourceARN"])


def main_wrapper():
    # List all rules in account
    paginator = events.get_paginator('list_rules')
    pages = paginator.paginate(EventBusName='default')
    for page in pages:
        for rule in page["Rules"]:
            if "ScheduleExpression" not in rule:
                # Skip for event pattern rules
                continue
            main(rule["Arn"], scheduled=True)


def main(arn, scheduled=False):
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

    # Skip for event pattern rules
    if "ScheduleExpression" not in response:
        logger.info("Rule does not have a schedule expression so will be ignored.")
        return

    expression = response["ScheduleExpression"]
    description = response.get("Description", "")
    role_arn = response.get("RoleArn", None)

    logger.info(f"Rule Cron Expression: {expression}")

    # Calculate new expression
    new_expression = calculate_expression(timezone, expression, scheduled=scheduled)

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


def calculate_expression(tz, exp, scheduled=False):
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
        if scheduled:
            # Scheduled event when DST not in effect should increment an hour
            split_exp = exp.split(" ")
            split_exp[1] = format_hour(split_exp[1], subtract=False)
            return " ".join(split_exp)
        # Otherwise expression should remain as per Terraform
        return exp


def format_hour(string, subtract=True):
    """Format the hour component of the expression."""
    if "*" in string or "/" in string:
        # Asterisk or forward slash wildcards
        return string
    elif "," in string:
        # Comma separated values
        hours = string.split(",")
        hours = [subtract_hour(h) if subtract else add_hour(h) for h in hours]
        return ",".join(hours)
    elif "-" in string:
        # Range of values
        hours = string.split("-")
        hours = [subtract_hour(h) if subtract else add_hour(h) for h in hours]
        return "-".join(hours)
    else:
        # Single value
        if subtract:
            return subtract_hour(string)
        return add_hour(string)


def subtract_hour(string):
    """Subtracts an hour from the string - 24 hour format."""
    if string == "0":
        return "23"
    hour = int(string)
    return str(hour - 1)


def add_hour(string):
    """Adds an hour from the string - 24 hour format."""
    if string == "23":
        return "0"
    hour = int(string)
    return str(hour + 1)
