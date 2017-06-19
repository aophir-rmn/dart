import logging

from datetime import datetime
from dart.engine.redshift.admin.cluster import RedshiftCluster
from dart.engine.redshift.command.copy import copy_from_s3, core_counts_by_instance_type
from dart.engine.redshift.command.ddl import create_schemas_and_tables, create_tracking_schema_and_table, \
    get_tracking_schema_and_table_name
from dart.model.subscription import SubscriptionElementState

_logger = logging.getLogger(__name__)


def consume_subscription(redshift_engine, datastore, action):
    """
    :type redshift_engine: dart.engine.redshift.redshift.RedshiftEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """
    _logger.info('starting consume_subscription')
    dart = redshift_engine.dart
    subscription = dart.get_subscription(action.data.args['subscription_id'])
    nudge_id = subscription.data.nudge_id
    dataset = dart.get_dataset(subscription.data.dataset_id)
    cluster = RedshiftCluster(redshift_engine, datastore)
    batch_size = cluster.get_number_of_nodes() * core_counts_by_instance_type.get(datastore.data.args['node_type'])
    conn = cluster.get_db_connection()
    try:
        _logger.info('setting up schemas, tables, s3_path generator')
        create_schemas_and_tables(conn, action, dataset)
        create_tracking_schema_and_table(conn, action)
        nudge_batches = None
        if nudge_id:
            most_recent_batch_id = get_most_recently_processed_nudge_batch(conn, action)
            nudge_batches = dart.get_latest_nudge_batches(nudge_id, most_recent_batch_id)
            if not nudge_batches:
                new_batch = dart.create_nudge_batch(nudge_id)
                if new_batch['BatchId']:
                    new_batch['State'] = 'UNCONSUMED'
                    nudge_batches = [new_batch]
            s3_path_and_updated_generator = _nudge_s3_path_and_updated_generator(dart, nudge_id, nudge_batches)
        else:
            most_recent_s3_path = get_most_recently_processed_s3_path(conn, action)
            s3_path_and_updated_generator = _s3_path_and_updated_generator(dart,
                                                                           subscription.id,
                                                                           action.id,
                                                                           most_recent_s3_path)
        copy_from_s3(dart, datastore, action, dataset, conn, batch_size, s3_path_and_updated_generator, nudge_id)
        if nudge_batches:
            for b in nudge_batches:
                if b['State'] == 'CONSUMED':
                    assert (dart.ack_nudge_elements(nudge_id, b['BatchId'])['Message'] == 'Success')
    finally:
        conn.close()


def get_most_recently_processed_s3_path(conn, action):
    sql = 'SELECT s3_path FROM %s.%s ORDER BY updated DESC, s3_path DESC LIMIT 1'
    result = list(conn.execute(sql % get_tracking_schema_and_table_name(action)))
    return result[0] if result else None


def get_most_recently_processed_nudge_batch(conn, action):
    sql = 'SELECT batch_id FROM %s.%s ORDER BY updated DESC LIMIT 1'
    result = list(conn.execute(sql % get_tracking_schema_and_table_name(action)))
    return result[0] if result else None


def _s3_path_and_updated_generator(dart, subscription_id, action_id, processed_after_s3_path):
    # first process anything we have missed (e.g. the cluster has been restored from a backup)
    if processed_after_s3_path:
        for e in dart.find_subscription_elements(subscription_id,
                                                 SubscriptionElementState.CONSUMED,
                                                 processed_after_s3_path):
            yield e.s3_path, e.updated

    dart.assign_subscription_elements(action_id)
    for e in dart.get_subscription_elements(action_id):
        yield e.s3_path, e.updated


def _nudge_s3_path_and_updated_generator(dart, nudge_subscription_id, batches):
    for batch in batches:
        for e in dart.get_nudge_batch_elements(nudge_subscription_id, batch['BatchId']):
            yield 's3://{bucket}/{key}'.format(bucket=e['Bucket'], key=e['Key']), \
                  datetime.utcnow(), \
                  batch['BatchId']
