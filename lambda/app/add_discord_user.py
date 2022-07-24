from eth_account.messages import encode_defunct
from web3 import Web3
import json
import boto3
import os

_lambda = boto3.client('lambda')
web3 = Web3()

dynamodb = boto3.resource('dynamodb')
discord_users = dynamodb.Table(os.environ['DISCORD_USERS_TABLE_NAME'])


def gen_status(status_code, body):
    return {
        'statusCode': status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST"
        },
        "body": json.dumps({'msg': body}),
    }


def handle(event, context):
    data = json.loads(event['body'])
    print("processing data")
    print(data)
    message = encode_defunct(text=f"address:{data['address']}\nusername:{data['username']}\ndiscriminator:{data['discriminator']}\nmember_id:{data['member_id']}")
    recovered_address = web3.eth.account.recover_message(message,
                                                         signature=data['signature'])
    #
    if data['address'] != recovered_address:
        gen_status('401', 'recovered address did not match address submitted with')

    item = {
        'address': data['address'],
        'username': data['username'],
        'discriminator': data['discriminator'],
        'member_id': data['member_id']
    }

    discord_users.put_item(Item=item)
    return gen_status(200, 'success')

