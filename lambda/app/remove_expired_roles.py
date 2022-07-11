import boto3
import datetime
import logging
import requests
import os
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
secret_manager = boto3.client('secretsmanager')

user_access = dynamodb.Table(os.environ['USER_ACCESS_TABLE_NAME'])
discord_users = dynamodb.Table(os.environ['DISCORD_USERS_TABLE_NAME'])

discord_auth_bot = secret_manager.get_secret_value(SecretId=os.environ['DISCORD_AUTH_BOT_ARN'])['SecretString']


def get_expired_user():
    current_time = datetime.datetime.now().strftime('%s')
    response = user_access.scan(
        FilterExpression=Attr('expires_timestamp').lt(int(current_time)) and Key('token_id').eq(1)
    )
    try:
        return response['Items']
    except KeyError as err:
        logging.error(
            err
        )


def get_discord(address):
    res = discord_users.get_item(Key={'address': address})
    try:
        return res['Item']
    except KeyError as err:
        logging.error(
            f"Address: {address} not found"
        )


guild_id = 994197138802229258
role_id = 994319465317670933


def handle(event, context):
    expired = get_expired_user()
    if len(expired) > 0:
        for ex in expired:
            user = get_discord(ex['address'])
            print(user)
            r = requests.delete(
                f"https://discord.com/api/v9/guilds/{guild_id}/members/{user['member_id']}/roles/{role_id}",
                headers={'Authorization': discord_auth_bot})
            user_access.delete_item(Key={"address": ex['address'], "token_id": ex['token_id']})
