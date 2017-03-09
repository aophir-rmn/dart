import logging
import os
from dart.client.python.dart_client import Dart
from dart.config.config import configuration
from dart.engine.es.metadata import ElasticsearchActionTypes
from dart.model.engine import Engine, EngineData

_logger = logging.getLogger(__name__)


def add_elasticsearch_engine(config):
    engine_config = config['engines']['elasticsearch_engine']
    opts = engine_config['options']
    dart = Dart(opts['dart_host'], opts['dart_port'], opts['dart_api_version'])
    assert isinstance(dart, Dart)

    _logger.info('saving elasticsearch_engine')

    engine_id = None
    for e in dart.get_engines():
        if e.data.name == 'elasticsearch_engine':
            engine_id = e.id

    ecs_task_definition = None if config['dart']['use_local_engines'] else {
        'family': 'dart-%s-elasticsearch_engine' % config['dart']['env_name'],
        'containerDefinitions': [
            {
                'name': 'dart-elasticsearch_engine',
                'cpu': 64,
                'memory': 256,
                'image': engine_config['docker_image'],
                'logConfiguration': {'logDriver': 'syslog'},
                'environment': [
                    {'name': 'DART_ROLE', 'value': 'worker:engine_elasticsearch'},
                    {'name': 'DART_CONFIG', 'value': engine_config['config']},
                    {'name': 'AWS_DEFAULT_REGION', 'value': opts['region']}
                ],
                'mountPoints': [
                    {
                        'containerPath': '/mnt/ecs_agent_data',
                        'sourceVolume': 'ecs-agent-data',
                        'readOnly': True
                    }
                ],
            }
        ],
        'volumes': [
            {
                'host': {'sourcePath': '/var/lib/ecs/data'},
                'name': 'ecs-agent-data'
            }
        ],
    }

    e1 = dart.save_engine(Engine(id=engine_id, data=EngineData(
        name='elasticsearch_engine',
        description='For Elasticsearch clusters',
        options_json_schema={
            'type': 'object',
            'properties': {
                'access_key_id': {
                    'type': 'string',
                    'default': '',
                    'oneOf': [
                        {
                            'minLength': 20,
                            'maxLength': 20,
                            # 20 character alpha numerical, all uppercase
                            'pattern': '^[A-Z0-9]{20}$'
                        },
                        {
                            'minLength': 0,
                            'maxLength': 0
                        }
                    ],
                    'description': 'the access_key_id for accessing this elasticsearch cluster. '
                                   + 'Leave blank to use Dart\'s instance profile credentials'
                },
                'secret_access_key': {
                    'type': 'string',
                    'default': '',
                    'oneOf': [
                        {
                            'minLength': 0,
                            'maxLength': 0
                        },
                        {
                            'minLength': 40,
                            'maxLength': 40,
                            # from AWS Security Blog on how to match secret access keys. 40 characters
                            'pattern': '(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])'
                        }
                    ],
                    'x-dart-secret': True,
                    'description': 'the secret_access_key for accessing this elasticsearch cluster. '
                                   + 'Leave blank to use Dart\'s instance profile credentials'
                },
                'endpoint': {
                    'type': 'string',
                    'minLength': 1,
                    'maxLength': 256,
                    'pattern': '^[a-zA-Z0-9]+[a-zA-Z0-9\-\.]*\.es\.amazonaws\.com$',
                    'description': 'The AWS Elasticsearch domain endpoint that you use to submit index and search requests.'
                },
            },
            'additionalProperties': False,
            'required': ['endpoint']
        },
        supported_action_types=[
            ElasticsearchActionTypes.data_check,
            ElasticsearchActionTypes.create_index,
            ElasticsearchActionTypes.create_mapping,
            ElasticsearchActionTypes.create_template,
            ElasticsearchActionTypes.delete_index,
            ElasticsearchActionTypes.delete_template,
            ElasticsearchActionTypes.force_merge_index,
        ],
        ecs_task_definition=ecs_task_definition
    )))
    _logger.info('saved elasticsearch_engine: %s' % e1.id)


if __name__ == '__main__':
    add_elasticsearch_engine(configuration(os.environ['DART_CONFIG']))
