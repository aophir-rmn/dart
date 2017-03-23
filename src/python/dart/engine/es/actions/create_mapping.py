import logging
import traceback
import json

from dart.engine.es.admin.cluster import ElasticsearchCluster

_logger = logging.getLogger(__name__)


def create_mapping(elasticsearch_engine, datastore, action):
    """
    :type elasticsearch_engine: dart.engine.es.es.ElasticsearchEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """

    cluster = ElasticsearchCluster(elasticsearch_engine, datastore)
    es = cluster.get_es_client()

    try:
        action = elasticsearch_engine.dart.patch_action(action, progress=.5)

        index = action.data.args.get('index')

        document_type = action.data.args['document_type']

        mapping = json.dumps(json.loads(action.data.args['mapping']))

        es.indices.put_mapping(index=index, doc_type=document_type, body=mapping)

        elasticsearch_engine.dart.patch_action(action, progress=1)
    except Exception as e:
        error_message = e.message + '\n\n\n' + traceback.format_exc()
        raise Exception('Elasticsearch create mapping failed to execute: %s' % error_message)
