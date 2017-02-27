import logging
import json
import traceback

from dart.engine.elasticsearch.admin.cluster import ElasticsearchCluster

_logger = logging.getLogger(__name__)


def create_index(elasticsearch_engine, datastore, action):
    """
    :type elasitcsearch_engine: dart.engine.elasticsearch.elasticsearch.ElasticsearchEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """

    cluster = ElasticsearchCluster(elasticsearch_engine, datastore)
    es = cluster.get_es_client()

    try:
        action = elasticsearch_engine.dart.patch_action(action, progress=.5)

        index = action.data.args['index']
        # ensure json is well-formed
        mapping = json.dumps(json.loads(action.data.args['mapping']))

        es.indices.create(index=index, body=mapping)

        elasticsearch_engine.dart.patch_action(action, progress=1)
    except Exception as e:
        error_message = e.message + '\n\n\n' + traceback.format_exc()
        raise Exception('Elasticsearch create mapping failed to execute: %s' % error_message)


