import logging

from dart.model.action import ActionType

_logger = logging.getLogger(__name__)


class ElasticsearchActionTypes(object):
    data_check = ActionType(
        name='data_check',
        description='Executes a user defined, Elasticsearch data check',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'default': '_all',
                    'description': 'The Elasticsearch index to perform the query on. '
                                   + 'Leave blank or explicitly set to "_all" to perform the query on all indices.'
                },
                'document_type': {
                    'type': ['string', 'null'],
                    'default': None,
                    'description': 'The Elasticsearch document type to perform the query on. '
                                   + 'Leave blank to perform the query on all document types.'
                },
                'query_body': {
                    'type': 'string',
                    'x-schema-form': {'type': 'textarea'},
                    'description': 'The Elasticsearch query should return a response that contains at least one result '
                                   + '("hits" in Elasticsearch terminology") for the data check to pass. '
                                   + 'https://www.elastic.co/guide/en/elasticsearch/reference/5.1/query-dsl.html'
                },
            },
            'additionalProperties': False,
            'required': ['query_body'],
        },
    )

    create_index = ActionType(
        name='create_index',
        description='Creates an Elasticsearch index',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'default': '_all',
                    'description': 'The Elasticsearch index to create.'
                },
                'mapping': {
                    'type': 'string',
                    'x-schema-form': {'type': 'textarea'},
                    'description': 'The Elasticsearch index mapping.'
                },
            },
            'additionalProperties': False,
            'required': ['index'],
        },
    )

    create_mapping = ActionType(
        name='create_mapping',
        description='Creates an Elasticsearch mapping',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'default': '_all',
                    'description': 'The Elasticsearch index to create the mapping for.'
                                   + 'Explicitly set to "_all" or leave blank to create the mapping for all indices.'
                },
                'document_type': {
                    'type': 'string',
                    'description': 'The Elasticsearch document type to create the mapping for.'
                },
                'mapping': {
                    'type': 'string',
                    'x-schema-form': {'type': 'textarea'},
                    'description': 'The Elasticsearch mapping.'
                },
            },
            'additionalProperties': False,
            'required': ['mapping', 'document_type'],
        },
    )

    create_template = ActionType(
        name='create_template',
        description='Creates an Elasticsearch template',
        params_json_schema={
            'type': 'object',
            'properties': {
                'template_name': {
                    'type': 'string',
                    'description': 'The Elasticsearch template name to create.'
                },
                'template': {
                    'type': 'string',
                    'x-schema-form': {'type': 'textarea'},
                    'description': 'The Elasticsearch template.'
                },
            },
            'additionalProperties': False,
            'required': ['template', 'template_name'],
        },
    )

    delete_index = ActionType(
        name='delete_index',
        description='Deletes an Elasticsearch index',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'default': '_all',
                    'description': 'The Elasticsearch index to delete.'
                }
            },
            'additionalProperties': False,
            'required': ['index'],
        },
    )

    delete_mapping = ActionType(
        name='delete_mapping',
        description='Deletes an Elasticsearch mapping',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'description': 'The Elasticsearch index to create the mapping for. '
                                   + 'Explicitly set to "_all" to delete the mapping for all indices.'
                },
                'document_type': {
                    'type': 'string',
                    'description': 'The Elasticsearch document type to delete the mapping for. '
                                   + 'Explicitly set to "_all" to delete the mapping for all document types.'

                }
            },
            'additionalProperties': False,
            'required': ['index', 'document_type'],
        },
    )

    delete_template = ActionType(
        name='delete_template',
        description='Deletes an Elasticsearch template',
        params_json_schema={
            'type': 'object',
            'properties': {
                'template_name': {
                    'type': 'string',
                    'description': 'The Elasticsearch template name to delete.'
                },
            },
            'additionalProperties': False,
            'required': ['template_name'],
        },
    )

    force_merge_index = ActionType(
        name='force_merge_index',
        description='Force merges an Elasticsearch index',
        params_json_schema={
            'type': 'object',
            'properties': {
                'index': {
                    'type': 'string',
                    'default': '_all',
                    'description': 'A comma-separated list of index names; use \"_all" or empty string to perform the operation on all indices.'
                },
                'flush': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Specify whether the index should be flushed after performing the operation'
                },
                'allow_no_indices': {
                  'type': 'boolean',
                  'default': False,
                  'description': 'Whether to ignore if a wildcard indices expression resolves into no concrete indices.'
                                 + '(This includes "_all" string or when no indices have been specified)'
                },
                'expand_wildcards': {
                    'type': 'string',
                    'default': 'open',
                    'pattern': '^(open|closed|none|all)$',
                    'description': 'Whether to expand wildcard expression to concrete indices that are open, closed or '
                                    + 'both. default is "open". valid choices are: "open", "closed", "none", "all"'
                },
                'max_num_segments': {
                    'type': ['integer', 'null'],
                    'default': None,
                    'description': 'The number of segments the index should be merged into (default: dynamic)'
                },
                'only_expunge_deletes': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Specify whether the operation should only expunge deleted documents'
                },
                'wait_for_merge': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Specify whether the request should block until the merge process is finished'
                }
            },
            'additionalProperties': False,
            'required': ['index'],
        },
    )