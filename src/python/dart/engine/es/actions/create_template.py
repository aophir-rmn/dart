import logging
import json
import traceback

from dart.engine.es.admin.cluster import ElasticsearchCluster

_logger = logging.getLogger(__name__)


def create_template(elasticsearch_engine, datastore, action):
    """
    :type elasticsearch_engine: dart.engine.es.es.ElasticsearchEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """

    cluster = ElasticsearchCluster(elasticsearch_engine, datastore)
    es = cluster.get_es_client()

    try:
        action = elasticsearch_engine.dart.patch_action(action, progress=.5)

        template_name = action.data.args['template_name']
        # ensure json is well-formed
        template = json.dumps(json.loads(action.data.args['template']))

        es.indices.put_template(name=template_name, body=template)

        elasticsearch_engine.dart.patch_action(action, progress=1)
    except Exception as e:
        error_message = e.message + '\n\n\n' + traceback.format_exc()
        raise Exception('Elasticsearch create template failed to execute: %s' % error_message)


