from dart.model.action import ActionType


class DynamoDBActionTypes(object):
    create_table = ActionType(
        name='create_table',
        description='creates a new DynamoDB table, where the hash key, sort key, attributes, and their types are '
                    'inferred from datastore\'s dataset',
        params_json_schema={
            'type': 'object',
            'properties': {
                'read_capacity_units': {'type': ['integer', 'null'], 'minimum': 1, 'default': 25, 'description': 'the initial read throughput'},
                'write_capacity_units': {'type': ['integer', 'null'], 'minimum': 1, 'default': 25, 'description': 'the initial write throughput'},
            },
            'additionalProperties': False,
            'required': ['read_capacity_units', 'write_capacity_units'],
        }
    )
    delete_table = ActionType(
        name='delete_table',
        description='deletes a DynamoDB table',
    )
    load_dataset = ActionType(
        name='load_dataset',
        description='loads the data from this datastore\'s dataset',
        params_json_schema={
            'type': 'object',
            'properties': {
                's3_path_start_prefix_inclusive_date_offset_in_seconds': {'type': ['integer', 'null'], 'default': 0, 'description': 'If specified, the date used in s3 path substitutions will be adjusted by this amount'},
                's3_path_start_prefix_inclusive': {
                    'type': ['string', 'null'],
                    'default': None,
                    'pattern': '^s3://.+$',
                    'description': 'The inclusive s3 path start prefix. The following values (with braces) will be '
                                   'substituted with the appropriate zero-padded values at runtime: {YEAR}, {MONTH}, '
                                   '{DAY}, {HOUR}, {MINUTE}, {SECOND}',
                },
                's3_path_end_prefix_exclusive_date_offset_in_seconds': {'type': ['integer', 'null'], 'default': 0, 'description': 'If specified, the date used in s3 path substitutions will be adjusted by this amount'},
                's3_path_end_prefix_exclusive': {
                    'type': ['string', 'null'],
                    'default': None,
                    'pattern': '^s3://.+$',
                    'description': 'The exclusive s3 path end prefix. The following values (with braces) will be '
                                   'substituted with the appropriate zero-padded values at runtime: {YEAR}, {MONTH}, '
                                   '{DAY}, {HOUR}, {MINUTE}, {SECOND}',
                },
                's3_path_regex_filter_date_offset_in_seconds': {'type': ['integer', 'null'], 'default': 0, 'description': 'If specified, the date used in s3 path substitutions will be adjusted by this amount'},
                's3_path_regex_filter': {
                    'type': ['string', 'null'],
                    'default': None,
                    'description': 'A regex pattern the s3 path must match. The following values (with braces) will be '
                                   'substituted with the appropriate zero-padded values at runtime: {YEAR}, {MONTH}, '
                                   '{DAY}, {HOUR}, {MINUTE}, {SECOND}',
                },
                'initial_write_capacity_units': {'type': ['integer', 'null'], 'description': 'leave blank to avoid changing this value'},
                'final_write_capacity_units': {'type': ['integer', 'null'], 'description': 'leave blank to avoid changing this value'},
                'write_capacity_utilization_percent': {
                    'type': ['number', 'null'],
                    'default': 0.5,
                    'minimum': 0.1,
                    'maximum': 1.5,
                    'description': 'the percentage of write capacity units to utilize'
                },
            },
            'additionalProperties': False,
            'required': [],
        }
    )
