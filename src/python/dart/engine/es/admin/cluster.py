import logging

import boto3
from requests_aws4auth import AWS4Auth
from dart.model.datastore import Datastore
from elasticsearch import Elasticsearch, RequestsHttpConnection

_logger = logging.getLogger(__name__)


class ElasticsearchCluster(object):
    def __init__(self, elasticsearch_engine, datastore):
        self.elasticsearch_engine = elasticsearch_engine
        self.datastore = datastore
        self.access_key_id = self.datastore.data.args.get('access_key_id')
        self.endpoint = self.datastore.data.args['endpoint']
        self.region = self.get_es_cluster_region()

        assert isinstance(datastore, Datastore)
        # the presence of workflow_datastore_id indicates this datastore was created from a template in a workflow
        dsid = datastore.data.workflow_datastore_id or self.datastore.id
        self.secret_access_key_kms = 'dart-datastore-%s-secret_access_key' % dsid

    def get_es_cluster_region(self):
        endpoint_parts = self.endpoint.split('.')

        if len(endpoint_parts) != 5:
            raise ValueError('Cannot parse region from es cluster endpoint: %s' % self.endpoint)

        region = endpoint_parts[1].lower()

        if region not in boto3.session.Session().get_available_regions('es'):
            raise ValueError('Invalid region for Elasticsearch service: %s' % region)

        return region

    def get_secret_access_key(self):
        return self.elasticsearch_engine.secrets.get(self.secret_access_key_kms)

    def get_es_client(self):
        secret_access_key = self.get_secret_access_key()

        if self.access_key_id and secret_access_key:
            auth = AWS4Auth(self.access_key_id,
                            self.get_secret_access_key(),
                            self.region,
                            'es')
        else:
            credentials = boto3.Session().get_credentials()

            auth = AWS4Auth(credentials.access_key,
                            credentials.secret_key,
                            self.region,
                            'es',
                            session_token=credentials.token)

        return Elasticsearch(
            hosts=[{'host': self.endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
