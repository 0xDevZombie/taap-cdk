import json
import decimal
import boto3
import os
import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import logging


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)


class ToolsUsers:
    """Encapsulates an Amazon DynamoDB table of tool users."""

    def __init__(self, dyn_resource, table):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = table

    def get_item(self, address, token_id):
        """
        Gets movie data from the table for a specific movie.

        :param address: The title of the movie.
        :param token_id: The release year of the movie.
        :return: The data about the requested movie.
        """
        try:
            response = self.table.get_item(Key={'address': address, 'token_id': token_id})
        except ClientError as err:
            logger.error(
                "Couldn't get movie %s from table %s. Here's why: %s: %s",
                address, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            try:
                return response['Item']
            except KeyError as err:
                logging.info(
                    f"No item in table for query: address: {address}, token_id: {token_id}"
                )


logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
tools_users_table = dynamodb.Table(os.environ['TOOLS_USERS_TABLE_NAME'])

tool_users = ToolsUsers(dynamodb, tools_users_table)


def handle(event, context):
    address = event["queryStringParameters"]['address'].lower()
    to_return = {'address': address}

    item_token_two = tool_users.get_item(address, 2)
    current_time = datetime.datetime.now().strftime('%s')
    if item_token_two:
        if current_time < item_token_two['expires_timestamp']:
            to_return['token_2_is_valid'] = True
        else:
            to_return['token_2_is_valid'] = False

    else:
        to_return['token_2_is_valid'] = False

    item_token_three = tool_users.get_item(address, 3)
    if item_token_three:
        if current_time < item_token_three['expires_timestamp']:
            to_return['token_3_is_valid'] = True
        else:
            to_return['token_3_is_valid'] = False
    else:
        to_return['token_3_is_valid'] = False

    return {
        "statusCode": 200,
        "body": json.dumps(to_return, cls=DecimalEncoder),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        }
    }
