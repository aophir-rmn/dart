from dart.schema.base import base_schema, tag_list_schema
from dart.schema.dataset import dataset_schema
from dart.schema.event import event_schema
from dart.schema.subscription import subscription_schema
from dart.schema.workflow import workflow_schema


def engine_schema():
    return base_schema({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'pattern': '^[a-zA-Z0-9_-]+$', 'maxLength': 50},
            'description': {'type': ['string', 'null']},
            'ecs_task_definition': {'type': ['object', 'null']},
            'ecs_task_definition_arn': {'type': ['string', 'null']},
            'options_json_schema': {'type': ['object', 'null']},
            'supported_action_types': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'params_json_schema': {'type': ['object', 'null']},
                    }
                },
                'minItems': 1,
            },
            'tags': tag_list_schema(),
        },
        'additionalProperties': False,
        'required': ['name', 'user_id']
    })


def subgraph_definition_schema(trigger_schemas, action_schemas, datastore_schema):
    return base_schema({
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'description': {'type': 'string'},
            'engine_name': {'type': 'string'},
            'related_type': {'type': 'string', 'maxLength': 50},
            'related_is_a': {'type': 'string', 'maxLength': 50},
            'actions': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': {'anyOf': action_schemas},
                'default': []
            },
            'datastores': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': datastore_schema,
                'default': []
            },
            'datasets': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': dataset_schema(),
                'default': []
            },
            'events': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': event_schema(),
                'default': []
            },
            'subscriptions': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': subscription_schema(),
                'default': []
            },
            'triggers': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': {'anyOf': trigger_schemas},
                'default': []
            },
            'workflows': {
                'x-schema-form': {'type': 'tabarray', 'title': "{{ value.name }}"},
                'type': 'array',
                'items': workflow_schema(),
                'default': []
            },
            'icon': {'type': ['string', 'null']},
            'md_icon': {'type': ['string', 'null']},
        },
        'additionalProperties': False,
        'required': ['name', 'engine_name', 'related_type', 'related_is_a']
    })
