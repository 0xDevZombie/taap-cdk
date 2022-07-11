import decimal
import json
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


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
