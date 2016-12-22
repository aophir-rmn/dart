ENTITY_IDENTIFIER_SQL_ = """
    SELECT DISTINCT *
    FROM (
        SELECT 'action', id, data ->> 'name'
          FROM action
         WHERE data ->> 'state' = 'TEMPLATE'
           AND id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'dataset', id, data ->> 'name' FROM dataset WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'datastore', id, data ->> 'name' FROM datastore WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'event', id, data ->> 'name' FROM event WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'subscription', id, data ->> 'name' FROM subscription WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'trigger', id, data ->> 'name' FROM trigger WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'

          UNION ALL

        SELECT 'workflow', id, data ->> 'name' FROM workflow WHERE id iLIKE '%' || :search || '%' OR data ->> 'name' iLIKE '%' || :search || '%'
    ) t
    LIMIT 20
"""
ENTITY_IDENTIFIER_SQL = ''.join(ENTITY_IDENTIFIER_SQL_.split('\n'))


DATASTORE_ONE_OFFS_SQL_ = """
  SELECT 'datastore', d.id, NULL, NULL, a.id, a.name, a.state, a.sub_type
    FROM datastore d
    JOIN LATERAL (
            SELECT e.id,
                   e.created,
                   CAST(e.data ->> 'order_idx' AS FLOAT) AS order_idx,
                   CASE WHEN e.data ->> 'state' = 'RUNNING' THEN CONCAT(e.data ->> 'name', CONCAT(' - ', CONCAT(CAST(100 * COALESCE(CAST(e.data ->> 'progress' AS FLOAT), 0.0) AS INT), '%')))
                       ELSE e.data ->> 'name'
                   END AS name,
                   e.data ->> 'state' AS state,
                   e.data ->> 'action_type_name' AS sub_type
              FROM action e
             WHERE e.data ->> 'datastore_id' = d.id
               AND e.data -> 'workflow_id' = 'null'
               AND e.created > NOW() - INTERVAL '1 day'
          ORDER BY e.created DESC
             LIMIT 10
    ) a
      ON TRUE
   WHERE d.id IN ({d_ids})
ORDER BY d.created, a.order_idx, a.created
"""
DATASTORE_ONE_OFFS_SQL = ''.join(DATASTORE_ONE_OFFS_SQL_.split('\n'))


WORKFLOW_INSTANCE_SQL_ = """
     SELECT 'workflow', w.id, wfis.id, wfis.state, a.id,
            CASE WHEN a.data ->> 'state' = 'RUNNING' THEN CONCAT(a.data ->> 'name', CONCAT(' - ', CONCAT(CAST(100 * COALESCE(CAST(a.data ->> 'progress' AS FLOAT), 0.0) AS INT), '%')))
                ELSE a.data ->> 'name'
            END,
            a.data ->> 'state', a.data ->> 'action_type_name' AS sub_type
       FROM workflow w
       JOIN LATERAL (
             SELECT wfi.id, wfi.created, wfi.data ->> 'state' AS state
               FROM workflow_instance wfi
              WHERE wfi.data ->> 'workflow_id' = w.id
           ORDER BY wfi.created DESC
              LIMIT CAST(w.data ->> 'concurrency' AS INT)
          ) wfis
         ON TRUE
  LEFT JOIN action a
         ON a.data ->> 'workflow_instance_id' = wfis.id
      WHERE w.id IN ({wf_ids})
   ORDER BY wfis.created, CAST(a.data ->> 'order_idx' AS FLOAT), a.created
"""
WORKFLOW_INSTANCE_SQL = ''.join(WORKFLOW_INSTANCE_SQL_.split('\n'))
