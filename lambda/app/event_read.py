import boto3
import os
from web3 import Web3
# from web3.middleware import geth_poa_middleware
import json
import requests
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
secret_manager = boto3.client('secretsmanager')
block_number = dynamodb.Table(os.environ['BLOCK_TABLE_NAME'])
user_access = dynamodb.Table(os.environ['USER_ACCESS_TABLE_NAME'])
discord_users = dynamodb.Table(os.environ['DISCORD_USERS_TABLE_NAME'])

INFURA_URL = secret_manager.get_secret_value(SecretId=os.environ['INFURA_URL_ARN'])['SecretString']
discord_auth_bot = secret_manager.get_secret_value(SecretId=os.environ['DISCORD_AUTH_BOT_ARN'])['SecretString']


def gen_status(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': body
    }


def getItem():
    try:
        response = block_number.get_item(Key={'app': 'taap'})
    except ClientError as err:
        # logger.error(
        #     "error",
        #     err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        try:
            return response['Item']
        except KeyError as err:
            logging.info(
                f"noitem"
            )
            return {"from_block": 0}


def get_user(address):
    res = discord_users.get_item(Key={'address': address})
    try:
        return res['Item']
    except KeyError as err:
        logging.error(
            f"Address: {address} not found"
        )


def handle(event, context):

    web3 = Web3(Web3.HTTPProvider(INFURA_URL))

    data = open('ABI.JSON')
    contract = json.load(data)
    myContract = web3.eth.contract(address="0x6743E037C176CAA49d495a3169F40779a8Dc1a8C", abi=contract['abi'])

    # web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    from_block = getItem()

    latest_block = web3.eth.get_block('latest').number

    block_number.put_item(
        Item={'app': 'taap', 'from_block': latest_block})

    transfer_filter = myContract.events.TokenRedeemed.createFilter(fromBlock=int(from_block['from_block']),
                                                                   toBlock=latest_block)
    for tx in transfer_filter.get_all_entries():
        expires = datetime.fromtimestamp(tx['args']['timestamp']) + timedelta(days=14)
        item = {'address': tx['args']['user'].lower(), 'burn_timestamp': tx['args']['timestamp'],
                'token_id': tx['args']['tokenId'], 'expires_timestamp': expires.strftime('%s')}


        if tx['args']['tokenId'] == 1:
            user = get_user(tx['args']['user'])
            if user:
                discord_auth_bot = secret_manager.get_secret_value(SecretId=os.environ['DISCORD_AUTH_BOT_ARN'])[
                    'SecretString']
                if discord_auth_bot[:3].lower() != 'bot':
                    return gen_status(401, 'DISCORD AUTH BOT NOT SET')

                guild_id = 898493032956055553
                role_id = 1000775589810143272
                r = requests.put(
                    f"https://discord.com/api/v9/guilds/{guild_id}/members/{user['member_id']}/roles/{role_id}",
                    headers={'Authorization': discord_auth_bot})
                if r.status_code == 204:
                    user_access.put_item(Item=item)
        else:
            user_access.put_item(
                Item=item)
