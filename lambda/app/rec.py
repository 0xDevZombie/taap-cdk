from eth_account.messages import encode_defunct
from web3 import Web3
import json
import boto3
import os
# INFURA_URL = 'https://rinkeby.infura.io/v3/d6ee5da27129452a8ed2fbfda614d1f9'
web3 = Web3()


data = {
    "address": "0x08Df5b728dE52e5016B26E7E31Db65bE9f564a8c",
    "username": "0xDevZombie.eth",
    "discriminator": "#4741",
    "member_id": "174251192715575296",
    "signature": "0xf6eddf6800ee9521172e029c0ee0aa77cb93ee84923d526e9151712a06bf0e801be353488dd9f13a33f1203dc753f4f91cc4ea523adb0c4e1538f3ce2b1356f31c"
}

message = encode_defunct(text=f"address:{data['address']}\nusername:{data['username']}\ndiscriminator:{data['discriminator']}\nmember_id:{data['member_id']}")
# message = encode_defunct(text=f"0xDevZombie.eth#474")
recovered_address = web3.eth.account.recover_message(message,
                                                     signature=data['signature'])

print(recovered_address)
