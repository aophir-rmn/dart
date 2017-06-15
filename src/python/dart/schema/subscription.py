from dart.model.subscription import SubscriptionState
from dart.schema.base import base_schema, email_list_schema, tag_list_schema


def subscription_schema():
    return base_schema({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'pattern': '^[a-zA-Z0-9_-]+$', 'maxLength': 50},
            'dataset_id': {'type': 'string'},
            'tags': tag_list_schema(),
            's3_path_start_prefix_inclusive': {'type': ['string', 'null'], 'default': None, 'pattern': '^s3://.+$', 'description': 'The inclusive s3 path start prefix'},
            's3_path_end_prefix_exclusive': {'type': ['string', 'null'], 'default': None, 'pattern': '^s3://.+$', 'description': 'The exclusive s3 path end prefix'},
            's3_path_regex_filter': {'type': ['string', 'null'], 'default': None, 'description': 'A regex pattern the s3 path must match'},
            'state': {'type': 'string', 'enum': SubscriptionState.all(), 'default': SubscriptionState.INACTIVE},
            'queued_time': {'type': ['string', 'null'], 'readonly': True},
            'generating_time': {'type': ['string', 'null'], 'readonly': True},
            'initial_active_time': {'type': ['string', 'null'], 'readonly': True},
            'failed_time': {'type': ['string', 'null'], 'readonly': True},
            'message_id': {'type': ['string', 'null'], 'default': None, 'readonly': True},
            'on_failure_email': email_list_schema(),
            'on_success_email': email_list_schema(),
            'nudge_id': {'type': ['string', 'null'], 'default': None, 'description': 'The corresponding nudge id for this subscription', 'readonly': True}
        },
        'additionalProperties': False,
        'required': ['name', 'dataset_id']
    })
