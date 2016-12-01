from dart.model.action import ActionType


class NoOpActionTypes(object):
    action_that_succeeds = ActionType(
        name='fake_action_that_succeeds',
        description='helps engineers develop and test'
    )
    action_that_fails = ActionType(
        name='fake_action_that_fails',
        description='helps engineers develop and test'
    )
    copy_hdfs_to_s3_action = ActionType(
        name='fake_copy_hdfs_to_s3',
        description='Copies data at the specified hdfs path to s3',
        params_json_schema={
            'type': 'object',
            'properties': {
                'source_hdfs_path': {'type': 'string', 'pattern': '^hdfs://.+$', 'description': 'The source hdfs path, e.g. hdfs:///user/hive/warehouse/table'},
                'destination_s3_path': {'type': 'string', 'pattern': '^s3://.+$', 'description': 'The destination s3 path, e.g. s3://bucket/prefix'},
            },
            'additionalProperties': False,
            'required': ['source_hdfs_path', 'destination_s3_path'],
        }
    )
    load_dataset = ActionType(
        name='fake_load_dataset',
        description='Copies the dataset from s3 to the datastore',
        params_json_schema={
            'type': 'object',
            'properties': {
                'dataset_id': {'type': 'string', 'description': 'The id of the dataset to load'},
            },
            'additionalProperties': False,
            'required': ['dataset_id'],
        }
    )
    consume_subscription = ActionType(
        name='consume_subscription',
        description='Consumes the next available dataset subscription elements',
        params_json_schema={
            'type': 'object',
            'properties': {
                'subscription_id': {'type': 'string', 'description': 'The id of the subscription to consume'},
            },
            'additionalProperties': False,
            'required': ['subscription_id'],
        }
    )
