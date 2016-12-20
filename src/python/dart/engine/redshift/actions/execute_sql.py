import logging

from dart.engine.redshift.admin.cluster import RedshiftCluster
from dart.engine.redshift.admin.utils import sanitized_query

_logger = logging.getLogger(__name__)


def execute_sql(redshift_engine, datastore, action):
    """
    :type redshift_engine: dart.engine.redshift.redshift.RedshiftEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """
    cluster = RedshiftCluster(redshift_engine, datastore)
    conn = cluster.get_db_connection()
    txn = conn.begin()
    try:
        action = redshift_engine.dart.patch_action(action, progress=.1)
        datastore_user_id = datastore.data.user_id if hasattr(datastore.data, 'user_id') else 'anonymous'
        sanitzed_sql = sanitized_query(action.data.args['sql_script'])

        # Adding  --USER-ID helps identify who this query run belongs to.
        sql_to_execute = "---USER_ID={user_id}\n{sanitzed_sql}".format(sanitzed_sql=sanitzed_sql, user_id=datastore_user_id)
        conn.execute(sql_to_execute)
        txn.commit()
        redshift_engine.dart.patch_action(action, progress=1)
    except:
        txn.rollback()
        raise
    finally:
        conn.close()
