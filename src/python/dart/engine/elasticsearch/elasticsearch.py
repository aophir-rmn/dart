import logging
import os
import traceback

from dart.client.python.dart_client import Dart
from dart.engine.elasticsearch.actions.data_check import data_check
from dart.engine.elasticsearch.actions.create_index import create_index
from dart.engine.elasticsearch.actions.create_template import create_template
from dart.engine.elasticsearch.actions.create_mapping import create_mapping
from dart.engine.elasticsearch.actions.delete_index import delete_index
from dart.engine.elasticsearch.actions.delete_template import delete_template
from dart.engine.elasticsearch.actions.delete_mapping import delete_mapping
from dart.engine.elasticsearch.actions.force_merge_index import force_merge_index
from dart.engine.elasticsearch.metadata import ElasticsearchActionTypes
from dart.model.engine import ActionResultState, ActionResult
from dart.service.secrets import Secrets
from dart.tool.tool_runner import Tool

_logger = logging.getLogger(__name__)


class ElasticsearchEngine(object):
    def __init__(self, kms_key_arn, secrets_s3_path, dart_host, dart_port, dart_api_version=1):

        self.dart = Dart(dart_host, dart_port, dart_api_version)
        self._action_handlers = {
            ElasticsearchActionTypes.data_check.name: data_check,
            ElasticsearchActionTypes.create_index.name: create_index,
            ElasticsearchActionTypes.create_template.name: create_template,
            ElasticsearchActionTypes.create_mapping.name: create_mapping,
            ElasticsearchActionTypes.delete_index.name: delete_index,
            ElasticsearchActionTypes.delete_template.name: delete_template,
            ElasticsearchActionTypes.delete_mapping.name: delete_mapping,
            ElasticsearchActionTypes.force_merge_index.name: force_merge_index,
        }
        self.secrets = Secrets(kms_key_arn, secrets_s3_path)

    def run(self):
        action_context = self.dart.engine_action_checkout(os.environ.get('DART_ACTION_ID'))
        action = action_context.action
        datastore = action_context.datastore

        state = ActionResultState.SUCCESS
        error_message = None
        try:
            action_type_name = action.data.action_type_name
            _logger.info('**** ElasticsearchEngine.run_action: %s', action_type_name)
            assert action_type_name in self._action_handlers, 'unsupported action: %s' % action_type_name
            handler = self._action_handlers[action_type_name]
            handler(self, datastore, action)

        except Exception as e:
            state = ActionResultState.FAILURE
            error_message = e.message + '\n\n\n' + traceback.format_exc()

        finally:
            self.dart.engine_action_checkin(action.id, ActionResult(state, error_message))


class ElasticsearchEngineEngineTaskRunner(Tool):
    def __init__(self):
        super(ElasticsearchEngineEngineTaskRunner, self).__init__(_logger, configure_app_context=False)

    def run(self):
        ElasticsearchEngine(**(self.dart_config['engines']['elasticsearch_engine']['options'])).run()


if __name__ == '__main__':
    ElasticsearchEngineEngineTaskRunner().run()
