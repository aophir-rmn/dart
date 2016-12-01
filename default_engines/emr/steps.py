import gzip
import json
import ntpath
import os
import shutil

from boto.emr import JarStep as BotoJarStep
from dart.model.base import dictable
from dart.model.dataset import FileFormat, RowFormat, Compression

from engine.emr import mapped_column_type

_title_data = lambda action_id, n, t: 'action_id=%s,step_num=%s,steps_total=%s' % (action_id, n, t)
_hive_args = ['hive-script', '--run-hive-script', '--args', '-f']
_script_runner_jar = 's3n://us-east-1.elasticmapreduce/libs/script-runner/script-runner.jar'
_command_runner_jar = 'command-runner.jar'


@dictable
class StepWrapper(object):
    def __init__(self, step, step_num, steps_total, action_considered_successful=False):
        """
        :type step: dart.engine.emr.steps.JarStep
        :type step_num: int
        :type steps_total: int
        :type action_considered_successful: bool
        """
        self.step = step
        self.step_num = step_num
        self.steps_total = steps_total
        self.action_considered_successful = action_considered_successful


@dictable
class JarStep(BotoJarStep):
    """
    This is a pass-through class that allows us to use @dictable for json serialization
    """
    def __init__(self, name, jar, main_class=None, action_on_failure='TERMINATE_JOB_FLOW', step_args=None):
        """
        :type name: str
        :type jar: str
        :type main_class: str
        :type action_on_failure: str
        :type step_args: list[str]
        """
        super(JarStep, self).__init__(name, jar, main_class, action_on_failure, step_args)


def prepare_step_paths(datastore, tempdir):
    current_path, current_file = ntpath.split(os.path.abspath(__file__))
    shutil.copytree(os.path.join(current_path, 'steps'), os.path.join(tempdir, 'steps'))
    local_step_path = '%s/steps/' % tempdir
    s3_step_path = datastore.data.s3_artifacts_path + '/steps'
    s3_temp_path = datastore.data.s3_artifacts_path + '/_temp'
    return local_step_path, s3_step_path, s3_temp_path


def s3distcp_files_step(s3_path_and_file_size_generator, table_name, dataset, s3_step_path, local_step_path, action_id,
                        step_num, steps_total):
    values = (action_id, dataset.data.name, dataset.id)
    manifest_path = os.path.join('misc', 's3distcp_manifest_for_action_%s_dataset_%s_%s.txt.gz' % values)
    local_manifest_path = os.path.join(local_step_path, manifest_path)
    s3_manifest_path = os.path.join(s3_step_path, manifest_path)

    empty_generator = True
    with gzip.open(local_manifest_path, 'wb') as f:
        for s3_path, file_size in s3_path_and_file_size_generator:
            empty_generator = False
            base_name = s3_path.split(dataset.data.location + '/')[1]
            values = (s3_path, base_name, dataset.data.location, file_size)
            f.write('{"path":"%s","baseName":"%s","srcDir":"%s","size":%s}\n' % values)
    assert not empty_generator, 'cannot create s3distcp manifest without s3 files'

    return StepWrapper(
        JarStep(
            name='dart: (%s) s3distcp dataset_%s_%s' % (
                _title_data(action_id, step_num, steps_total), dataset.data.name, dataset.id
            ),
            jar='command-runner.jar',
            action_on_failure='CONTINUE',
            step_args=[
                's3-dist-cp', '--src', dataset.data.location, '--dest', 'hdfs:///user/hive/warehouse/%s/' % table_name,
                '--copyFromManifest', '--previousManifest', s3_manifest_path,
            ]
        ),
        step_num,
        steps_total
    )


def python_copy_hdfs_to_s3(s3_step_path, src, dest, s3_temp_path, action_id, step_num, steps_total):
    return StepWrapper(
        JarStep(
            name='dart: (%s) s3distcp_hdfs_to_s3.py' % _title_data(action_id, step_num, steps_total),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[s3_step_path + '/python/s3distcp_hdfs_to_s3.py', src, dest, s3_temp_path],
        ),
        step_num,
        steps_total
    )


def hive_table_definition_step(table_name, dataset, s3_step_path, local_step_path, action_id, external, step_num, steps_total):
    column_definitions = ',\n  '.join(['%s %s' % (c.name, mapped_column_type(c)) for c in dataset.data.columns])
    partitions = ', '.join(['%s %s' % (c.name, mapped_column_type(c)) for c in (dataset.data.partitions or [])])

    df = dataset.data.data_format
    if df.file_format.upper() == FileFormat.PARQUET:
        data_format = 'STORED AS PARQUET'

    elif df.file_format.upper() == FileFormat.RCFILE:
        data_format = 'ROW FORMAT SERDE "org.apache.hadoop.hive.serde2.columnar.ColumnarSerDe" STORED AS RCFILE'

    elif df.file_format.upper() == FileFormat.TEXTFILE:
        if df.row_format.upper() == RowFormat.REGEX:
            vs = (json.dumps(df.regex_input), json.dumps(df.regex_output))
            data_format = "ROW FORMAT SERDE 'org.apache.hadoop.hive.contrib.serde2.RegexSerDe'\n" +\
                          'WITH SERDEPROPERTIES ("input.regex" = %s, "output.format.string" = %s)' % vs

        elif df.row_format.upper() == RowFormat.DELIMITED:
            sp = '"separatorChar" = %s' % json.dumps(df.delimited_by)
            qt = '"quoteChar" = %s' % json.dumps(df.quoted_by) if df.quoted_by else ''
            es = '"escapeChar" = %s' % json.dumps(df.escaped_by) if df.escaped_by else ''
            ns = '"nullString" = %s' % json.dumps(df.null_string) if df.null_string else ''
            props_list = [sp]
            if qt: props_list.append(qt)
            if es: props_list.append(es)
            if ns: props_list.append(ns)
            props = ', '.join(props_list)
            data_format = "ROW FORMAT SERDE 'com.bizo.hive.serde.csv.RmnCsvSerde'\nWITH SERDEPROPERTIES (%s)" % props

        elif df.row_format.upper() == RowFormat.JSON:
            column_definitions = 'json STRING'
            data_format = ''

        else:
            raise Exception('unsupported row format: %s' % json.dumps(df.to_dict()))

    elif df.file_format.upper() == 'DYNAMODB_TABLE':
        data_format = (
            "STORED BY 'org.apache.hadoop.hive.dynamodb.DynamoDBStorageHandler'\n"
            "TBLPROPERTIES (\n"
            '  "dynamodb.table.name" = "{table_name}",\n'
            '  "dynamodb.column.mapping" = "{mapping}"\n'
            ")"
        ).format(
            table_name=table_name,
            mapping=','.join(['%s:%s' % (c.name, c.name) for c in dataset.data.columns])
        )

    else:
        raise Exception('unsupported file format: %s' % json.dumps(df.to_dict()))

    contents = '\nCREATE {external} TABLE IF NOT EXISTS {table_name} (\n' +\
               '{column_definitions}\n' +\
               ')\n' +\
               '{partitions}\n' +\
               '{data_format}\n' +\
               '{skip_rows};\n'

    hive_table_definition_path = os.path.join(local_step_path, 'hive', 'table_%s.hql' % table_name)
    with open(hive_table_definition_path, 'w') as f:
        contents = contents.format(
            external='EXTERNAL' if external else '',
            table_name=table_name,
            column_definitions=column_definitions,
            partitions='PARTITIONED BY (%s)' % partitions if partitions else '',
            data_format=data_format,
            skip_rows="TBLPROPERTIES ('skip.header.line.count'='%s')" % df.num_header_rows if df.num_header_rows else ''
        )
        f.write(contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) table_%s.hql' % (_title_data(action_id, step_num, steps_total), table_name),
            jar=_command_runner_jar,
            action_on_failure='CONTINUE',
            step_args=_hive_args + [s3_step_path + '/hive/table_%s.hql' % table_name],
        ),
        step_num,
        steps_total
    )


def python_fix_partition_folder_names(table_name, partitions, s3_step_path, action_id, step_num, steps_total):
    hdfs_root = 'hdfs:///user/hive/warehouse/' + table_name
    partition_names = ','.join([p.name for p in partitions])
    return StepWrapper(
        JarStep(
            name='dart: (%s) fix_partition_folder_names.py' % _title_data(action_id, step_num, steps_total),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[s3_step_path + '/python/fix_partition_folder_names.py', hdfs_root, partition_names],
        ),
        step_num,
        steps_total
    )


def hive_copy_to_table(source_dataset, source_table_name, destination_dataset, destination_table_name, s3_step_path,
                       local_step_path, action_id, set_hive_vars, step_num, steps_total):
    hive_source_path = os.path.join(local_step_path, 'hive', 'copy_to_table.hql')
    hive_target_path = os.path.join(local_step_path, 'hive', 'copy_to_table_%s.hql' % destination_table_name)
    with open(hive_source_path, 'r') as s, open(hive_target_path, 'w') as t:
        contents = s.read().format(
            source_table_name=source_table_name,
            destination_table_name=destination_table_name,
            partitions=get_partitions(source_dataset),
            columns=get_columns(source_dataset, destination_dataset),
            compression=get_emr_compression(destination_dataset),
            set_hive_vars=set_hive_vars if set_hive_vars else ''
        )
        t.write(contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) copy_to_table_%s.hql (from %s)' % (
                _title_data(action_id, step_num, steps_total), destination_table_name, source_table_name
            ),
            jar=_command_runner_jar,
            action_on_failure='CONTINUE',
            step_args=_hive_args + [s3_step_path + '/hive/copy_to_table_%s.hql' % destination_table_name],
        ),
        step_num,
        steps_total
    )


def get_columns(source_dataset, destination_dataset):
    source_columns = source_dataset.data.columns
    destination_columns = destination_dataset.data.columns
    columns = ',\n'.join([cast(sc, dc) for sc, dc in zip(source_columns, destination_columns)])
    if source_dataset.data.partitions:
        columns += ',\n' + ',\n'.join(['  ' + p.name for p in source_dataset.data.partitions])
    return columns


def get_partitions(dataset):
    return 'PARTITION (%s)' % ', '.join([p.name for p in dataset.data.partitions]) if dataset.data.partitions else ''


def get_emr_compression(dataset):
    if dataset.data.compression == Compression.NONE:
        return ''
    compression = 'SET hive.exec.compress.output=true;\n' + 'SET mapred.output.compression.type=BLOCK;\n'
    if dataset.data.compression == Compression.SNAPPY:
        return compression + 'SET mapred.output.compression.codec=org.apache.hadoop.io.compress.SnappyCodec;'
    if dataset.data.compression == Compression.GZIP:
        return compression + 'SET mapred.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec;'
    raise Exception('unsupported compression: %s' % dataset.data.compression)


def cast(source_column, destination_column):
    expression = source_column.name
    if source_column.path:
        expression = "get_json_object(json, '$.%s')" % source_column.path

    if mapped_column_type(destination_column) == 'STRING':
        return expression

    # Impala only supports timestamp, so we convert all to it
    if destination_column.data_type.upper() in ['TIMESTAMP', 'DATETIME', 'DATE']:
        if destination_column.date_pattern.upper() == 'UNIX_TIMESTAMP_SECONDS':
            return "CAST(CAST(%s AS BIGINT)*1000 AS TIMESTAMP)" % expression
        if destination_column.date_pattern.upper() == 'UNIX_TIMESTAMP_MILLIS':
            return "CAST(CAST(%s AS BIGINT) AS TIMESTAMP)" % expression
        if destination_column.date_pattern:
            return 'CAST(unix_timestamp(%s, "%s")*1000 AS TIMESTAMP)' % (expression, destination_column.date_pattern)
        values = (destination_column.data_type, destination_column.date_pattern)
        raise Exception('unsupported date type or pattern: format=%s, pattern=%s' % values)

    return "CAST(%s AS %s)" % (expression, mapped_column_type(destination_column))


def hive_msck_repair_table_step(table_name, s3_step_path, action_id, step_num, steps_total):
    return StepWrapper(
        JarStep(
            name='dart: (%s) command_msck_repair_table.hql (%s)' % (
                _title_data(action_id, step_num, steps_total), table_name
            ),
            jar=_command_runner_jar,
            action_on_failure='CONTINUE',
            step_args=_hive_args + [
                s3_step_path + '/hive/command_msck_repair_table.hql', '-d', 'TABLE=%s' % table_name
            ],
        ),
        step_num,
        steps_total
    )


def hive_run_script_contents_step(script_contents, s3_step_path, local_step_path, action_id, step_num, steps_total):
    hive_script_path = os.path.join(local_step_path, 'hive', 'run_hive_script_%s.hql' % action_id)
    with open(hive_script_path, 'w') as f:
        f.write(script_contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) run_hive_script_%s.hql' % (_title_data(action_id, step_num, steps_total), action_id),
            jar=_command_runner_jar,
            action_on_failure='CONTINUE',
            step_args=_hive_args + [s3_step_path + '/hive/run_hive_script_%s.hql' % action_id],
        ),
        step_num,
        steps_total
    )


def impala_copy_to_table(source_dataset, source_table_name, destination_dataset, destination_table_name, s3_step_path,
                         local_step_path, action_id, step_num, steps_total):
    impala_source_path = os.path.join(local_step_path, 'impala', 'copy_to_table.sql')
    impala_target_path = os.path.join(local_step_path, 'impala', 'copy_to_table_%s.sql' % destination_table_name)
    with open(impala_source_path, 'r') as s, open(impala_target_path, 'w') as t:
        contents = s.read().format(
            source_table_name=source_table_name,
            destination_table_name=destination_table_name,
            partitions=get_partitions(source_dataset),
            columns=get_columns(source_dataset, destination_dataset),
            compression=destination_dataset.data.compression
        )
        t.write(contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) copy_to_table_%s.sql (from %s)' % (
                _title_data(action_id, step_num, steps_total), destination_table_name, source_table_name
            ),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[
                s3_step_path + '/python/run_impala_script.py',
                s3_step_path + '/impala/copy_to_table_%s.sql' % destination_table_name
            ],
        ),
        step_num,
        steps_total
    )


def impala_run_script_contents_step(script_contents, s3_step_path, local_step_path, action_id, step_num, steps_total):
    impala_script_path = os.path.join(local_step_path, 'impala', 'run_impala_script_%s.sql' % action_id)
    with open(impala_script_path, 'w') as f:
        f.write(script_contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) run_impala_script_%s.sql' % (_title_data(action_id, step_num, steps_total), action_id),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[
                s3_step_path + '/python/run_impala_script.py',
                s3_step_path + '/impala/run_impala_script_%s.sql' % action_id
            ],
        ),
        step_num,
        steps_total
    )


def impala_invalidate_metadata_step(s3_step_path, action_id, step_num, steps_total):
    return StepWrapper(
        JarStep(
            name='dart: (%s) command_invalidate_metadata.sql' % _title_data(action_id, step_num, steps_total),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[
                s3_step_path + '/python/run_impala_script.py',
                s3_step_path + '/impala/command_invalidate_metadata.sql'
            ],
        ),
        step_num,
        steps_total
    )


def pyspark_run_script_contents_step(script_contents, s3_step_path, local_step_path, action_id, step_num, steps_total):
    pyspark_script_path = os.path.join(local_step_path, 'misc', 'run_pyspark_script_%s.py' % action_id)
    with open(pyspark_script_path, 'w') as f:
        f.write(script_contents)

    return StepWrapper(
        JarStep(
            name='dart: (%s) run_pyspark_script_%s.py' % (_title_data(action_id, step_num, steps_total), action_id),
            jar=_script_runner_jar,
            action_on_failure='CONTINUE',
            step_args=[
                s3_step_path + '/python/run_pyspark_script.py',
                s3_step_path + '/misc/run_pyspark_script_%s.py' % action_id
            ],
        ),
        step_num,
        steps_total
    )
