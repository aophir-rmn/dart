import logging

from dart.engine.redshift.admin.cluster import RedshiftCluster
from dart.engine.redshift.admin.utils import sanitized_query
_logger = logging.getLogger(__name__)


def cluster_maintenance (redshift_engine, datastore, action):
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

        sql_query = ''
        if(action.data.args['Retention_Policy']):
            rows = ''
            try:
                rows = list(conn.execute("Select schema_name, table_name, column_name, retention_days from dart.retention_policy;"))[0]

            except:
                raise Exception(
                    'The table dart.retention_policy doesn\'t exist or there is an error with the connection.')

            for row in rows:
                sql = 'Delete FROM {0}.{1} where DATEDIFF(day, {2}, current_date) > {3}'
                args = row[0], row[1], row[2], row[3]
                conn.execute(sql.format(*args))

        action = redshift_engine.dart.patch_action(action, progress=.3)
        if(action.data.args['vacuum']):
            if(not check_if_vacuum_is_running(conn)):
                run_vacuum(conn)
        action = redshift_engine.dart.patch_action(action, progress=.6)
        if(action.data.args['analyze']):
            run_analyze(conn)

        txn.commit()
        redshift_engine.dart.patch_action(action, progress=1)
    except:
        txn.rollback()
        raise
    finally:
        conn.close()

def run_analyze(conn):
    statements = []
    query = """SELECT DISTINCT 'analyze ' + feedback_tbl.schema_name + '."' + feedback_tbl.table_name + '" ; '
                                    + '/* '+ ' Table Name : ' + info_tbl."schema" + '.\"' + info_tbl."table"
                                        + '\", Stats_Off : ' + CAST(info_tbl."stats_off" AS VARCHAR(10)) + ' */ ;'
            FROM ((SELECT TRIM(n.nspname) schema_name,
                  c.relname table_name
           FROM (SELECT TRIM(SPLIT_PART(SPLIT_PART(a.plannode,':',2),' ',2)) AS Table_Name,
                        COUNT(a.query),
                        DENSE_RANK() OVER (ORDER BY COUNT(a.query) DESC) AS qry_rnk
                 FROM stl_explain a,
                      stl_query b
                 WHERE a.query = b.query
                 AND   CAST(b.starttime AS DATE) >= dateadd (DAY,30,CURRENT_DATE)
                 AND   a.userid > 1
                 AND   a.plannode LIKE '%%missing statistics%%'
                 AND   a.plannode NOT LIKE '%%_bkp_%%'
                 GROUP BY Table_Name) miss_tbl
             LEFT JOIN pg_class c ON c.relname = TRIM (miss_tbl.table_name)
             LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
           WHERE miss_tbl.qry_rnk <= 200)
           -- Get the top N rank tables based on the stl_alert_event_log alerts
           UNION
           SELECT schema_name,
                  table_name
           FROM (SELECT TRIM(n.nspname) schema_name,
                        c.relname table_name,
                        DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS qry_rnk,
                        COUNT(*)
                 FROM stl_alert_event_log AS l
                   JOIN (SELECT query,
                                tbl,
                                perm_table_name
                         FROM stl_scan
                         WHERE perm_table_name <> 'Internal Worktable'
                         GROUP BY query,
                                  tbl,
                                  perm_table_name) AS s ON s.query = l.query
                   JOIN pg_class c ON c.oid = s.tbl
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                 WHERE l.userid > 1
                 AND   l.event_time >= dateadd (DAY,30,CURRENT_DATE)
                 AND   l.Solution LIKE '%%ANALYZE command%%'
                 GROUP BY TRIM(n.nspname),
                          c.relname) anlyz_tbl
           WHERE anlyz_tbl.qry_rnk < 200) feedback_tbl
      JOIN svv_table_info info_tbl
        ON info_tbl.schema = feedback_tbl.schema_name
       AND info_tbl.table = feedback_tbl.table_name
    WHERE info_tbl.stats_off::DECIMAL (32,4) > 10::DECIMAL (32,4)

    ORDER BY info_tbl.size ASC  ;"""
    analyze_statements = list(conn.execute(query))[0]

    print analyze_statements
    for analyze_statement in analyze_statements:
        print analyze_statement
        statements.append(analyze_statement[0])

    if not run_commands(conn, statements):
        return 'ERROR'

def check_if_vacuum_is_running(conn):
    query = """Select count(1) from SVV_VACUUM_PROGRESS
               where time_remaining_estimate IS NOT NULL"""
    rows = list(conn.execute(query))[0]
    for row in rows:
        if int(row[0]) > 0:
            return True
    return False

def run_vacuum(conn):
    statements = []
    query = """Select Distinct query from
    (
    SELECT  DISTINCT \"schema_name\", 'vacuum ' + \"schema_name\" + '.' + \"table_name\" + ';' as query
    FROM   (SELECT TRIM(n.nspname)             schema_name,
                   c.relname                   table_name,
                   DENSE_RANK()
                     OVER (
                       ORDER BY COUNT(*) DESC) AS qry_rnk,
                   Count(*)
            FROM   stl_alert_event_log AS l
                   JOIN (SELECT query,
                                tbl,
                                perm_table_name
                         FROM   stl_scan
                         WHERE  perm_table_name <> 'Internal Worktable'
                         GROUP  BY query,
                                   tbl,
                                   perm_table_name) AS s
                     ON s.query = l.query
                   JOIN pg_class c
                     ON c.oid = s.tbl
                   JOIN PG_CATALOG.pg_namespace n
                     ON n.oid = c.relnamespace
            WHERE  l.userid > 1
                   AND l.event_time >= DATEADD(DAY, 30  , CURRENT_DATE)
                   AND l.Solution LIKE '%VACUUM command%'
            GROUP  BY TRIM(n.nspname),
                      c.relname) anlyz_tbl
    WHERE  anlyz_tbl.qry_rnk < 200

    UNION

    SELECT DISTINCT \"schema\" as schema_name, 'vacuum ' + \"schema\" + '.' + \"table\" + ';' as query
    FROM   svv_table_info
    WHERE
      ( unsorted > 10 OR stats_off > 10 )
      )
      where schema_name NOT IN ('metadata')
      """
    vacuum_statements = list(conn.execute(query))[0]
    print vacuum_statements
    for vs in vacuum_statements:
        print vs
        statements.append(vs[0])

    if not run_commands(conn, statements):
        return 'ERROR'


def run_commands(conn, commands):
    old_isolation_level = conn.isolation_level
    conn.set_isolation_level(0)
    for idx, c in enumerate(commands, start=1):
        if c != None:

            print('Running %s out of %s commands: %s' % (idx, len(commands), c))
            try:
                print(c)
                conn.execute(c)
                print('Success.')
            except Exception as e:
                # cowardly bail on errors
                print e
                conn.set_isolation_level(old_isolation_level)
                conn.rollback()
                return False

    conn.set_isolation_level(old_isolation_level)
    return True