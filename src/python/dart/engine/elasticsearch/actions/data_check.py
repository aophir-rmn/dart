import logging
import json
import traceback
import operator

from dart.engine.elasticsearch.admin.cluster import ElasticsearchCluster

_logger = logging.getLogger(__name__)


OPS = {
    '<=': operator.le,
    '<': operator.lt,
    '>=': operator.ge,
    '>': operator.ge,
    '==': operator.eq,
    '!=': operator.ne
}

def data_check(elasticsearch_engine, datastore, action):
    """
    :type elasitcsearch_engine: dart.engine.elasticsearch.elasticsearch.ElasticsearchEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """

    cluster = ElasticsearchCluster(elasticsearch_engine, datastore)
    es = cluster.get_es_client()

    try:
        action = elasticsearch_engine.dart.patch_action(action, progress=.5)
        # ensure json is well-formed
        query_body = json.dumps(json.loads(action.data.args['query_body']))

        op = OPS[action.data.args['operator']]

        expected_count = action.data.args['expected_count']

        valid = es.indices.validate_query(index=action.data.args['index'],
                                          doc_type=action.data.args['document_type'],
                                          body=query_body).get('valid')

        if not valid:
            raise Exception('Elasticsearch data check query is invalid.')

        response = es.count(index=action.data.args['index'],
                            doc_type=action.data.args['document_type'],
                            body=query_body)

        if op(response['count'], expected_count):
            elasticsearch_engine.dart.patch_action(action, progress=1)
        else:
            raise Exception('Elasticsearch data_check[name=%s] failed. Expected: %d %s %d' % (action.data.name,
                                                                                              response['count'],
                                                                                              action.data.args['operator'],
                                                                                              expected_count))
    except Exception as e:
        error_message = e.message + '\n\n\n' + traceback.format_exc()
        raise Exception('Elasticsearch data check failed to execute: %s' % error_message)

