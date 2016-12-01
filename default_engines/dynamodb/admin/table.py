import boto3
from retrying import retry
from botocore.exceptions import WaiterError


def _retry_waiter_error(exception):
    if isinstance(exception, WaiterError):
        return True
    return False


class DynamoDBTable(object):
    def __init__(self, table_name):
        self.table_name = table_name

    def create(self, attribute_definitions, key_schema, read_capacity_units, write_capacity_units):
        provisioned_throughput = {'ReadCapacityUnits': read_capacity_units, 'WriteCapacityUnits': write_capacity_units}
        boto3.client('dynamodb').create_table(
            AttributeDefinitions=attribute_definitions,
            KeySchema=key_schema,
            ProvisionedThroughput=provisioned_throughput,
            TableName=self.table_name,
        )
        self.wait_for_table_active()

    def delete(self):
        boto3.client('dynamodb').delete_table(TableName=self.table_name)
        self.wait_for_table_not_exists()

    def set_write_capacity_units(self, write_capacity_units):
        dynamodb_client = boto3.client('dynamodb')
        response = dynamodb_client.describe_table(TableName=self.table_name)
        read_capacity_units = response['Table']['ProvisionedThroughput']['ReadCapacityUnits']
        provisioned_throughput = {'ReadCapacityUnits': read_capacity_units, 'WriteCapacityUnits': write_capacity_units}
        dynamodb_client.update_table(TableName=self.table_name, ProvisionedThroughput=provisioned_throughput)
        self.wait_for_table_active()

    @retry(wait_fixed=10000, stop_max_attempt_number=7, retry_on_exception=_retry_waiter_error)
    def wait_for_table_active(self):
        boto3.client('dynamodb').get_waiter('table_exists').wait(TableName=self.table_name)

    @retry(wait_fixed=10000, stop_max_attempt_number=7, retry_on_exception=_retry_waiter_error)
    def wait_for_table_not_exists(self):
        boto3.client('dynamodb').get_waiter('table_not_exists').wait(TableName=self.table_name)
