import functools
import shutil
import tempfile

import boto
from engine.emr import dynamodb_column_type

from engine.emr import run_steps
from engine.emr import prepare_step_paths, python_fix_partition_folder_names, hive_copy_to_table, \
    impala_copy_to_table, hive_run_script_contents_step, StepWrapper
from engine.emr import s3distcp_files_step, hive_table_definition_step,\
    hive_msck_repair_table_step, impala_invalidate_metadata_step
from dart.model.dataset import Dataset, DataFormat, RowFormat, DataType, FileFormat, Compression, Column
from dart.util.s3 import yield_s3_keys, get_s3_path, s3_copy_recursive
from dart.util.s3 import get_bucket


def load_dataset(emr_engine, datastore, action):
    """
    :type emr_engine: dart.engine.emr.emr.EmrEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """
    dataset = emr_engine.dart.get_dataset(action.data.args['dataset_id'])
    generator = load_dataset_s3_path_and_file_size_generator(emr_engine, action, dataset)
    dry_run = datastore.data.args['dry_run']
    steps = prepare_load_dataset_steps(dry_run, action.data.args, datastore, dataset, action.id, generator)
    if dry_run:
        emr_engine.dart.patch_action(action, progress=1, extra_data={'steps': [s.to_dict() for s in steps]})
        return

    run_steps(emr_engine, datastore, action, steps)
    emr_engine.dart.patch_action(action, progress=1)


def prepare_load_dataset_steps(dry_run, args_by_name, datastore, dataset, action_id, s3_path_and_file_size_gen,
                               target_is_dynamodb=False):
    """ :type dataset: dart.model.dataset.Dataset """

    def add_to(step_partials, step_num, func, *args):
        # add all params except the last one, which is the total steps (known at the end)
        step_partials.append(functools.partial(func, *(list(args) + [step_num])))
        return step_num + 1

    def stage_table_not_needed(ds, file_format, row_format, compression, delimited_by, quoted_by,
                               escaped_by, null_string):
        """ :type ds: dart.model.dataset.Dataset """
        return file_format == ds.data.data_format.file_format\
            and row_format == ds.data.data_format.row_format\
            and compression == ds.data.compression\
            and delimited_by == ds.data.data_format.delimited_by\
            and quoted_by == ds.data.data_format.quoted_by\
            and escaped_by == ds.data.data_format.escaped_by\
            and null_string == ds.data.data_format.null_string

    # some steps require producing a dataset specific file based on a template, so we will copy all to a tempdir
    tempdir = tempfile.mkdtemp()
    try:
        local_step_path, s3_step_path, s3_temp_path = prepare_step_paths(datastore, tempdir)
        target_table_name = args_by_name.get('target_table_name') or dataset.data.table_name
        target_file_format = args_by_name.get('target_file_format') or dataset.data.data_format.file_format
        target_row_format = args_by_name.get('target_row_format') or dataset.data.data_format.row_format
        target_compression = args_by_name.get('target_compression') or dataset.data.compression
        target_delimited_by = args_by_name.get('target_delimited_by') or dataset.data.data_format.delimited_by
        target_quoted_by = args_by_name.get('target_quoted_by') or dataset.data.data_format.quoted_by
        target_escaped_by = args_by_name.get('target_escaped_by') or dataset.data.data_format.escaped_by
        target_null_string = args_by_name.get('target_null_string') or dataset.data.data_format.null_string

        stage_table_name = target_table_name + '_stage_for_action_' + action_id
        staging_not_needed = stage_table_not_needed(dataset, target_file_format, target_row_format, target_compression,
                                                    target_delimited_by, target_quoted_by, target_escaped_by, target_null_string)
        first_table_name = target_table_name if staging_not_needed and not target_is_dynamodb else stage_table_name

        drop_table_names = []
        step_funcs = []
        i = 1

        # ------------------------------------------------------------------------------------------------------------
        # all code paths below require copying the data to HDFS, and lowercasing the table is required because of hive
        # ------------------------------------------------------------------------------------------------------------
        i = add_to(step_funcs, i, s3distcp_files_step, s3_path_and_file_size_gen, first_table_name.lower(), dataset, s3_step_path, local_step_path, action_id)

        # ------------------------------------------------------------------------------------------------------------
        # not all folder structures on s3 are hive compatible... if not, rename directories after copying
        # ------------------------------------------------------------------------------------------------------------
        if dataset.data.partitions and not dataset.data.hive_compatible_partition_folders:
            i = add_to(step_funcs, i, python_fix_partition_folder_names, first_table_name.lower(), dataset.data.partitions, s3_step_path, action_id)

        # ------------------------------------------------------------------------------------------------------------
        # special case to share functionality with the dynamodb_engine
        # ------------------------------------------------------------------------------------------------------------
        if target_is_dynamodb:
            dyn_dataset = Dataset.from_dict(dataset.to_dict())
            assert isinstance(dyn_dataset, Dataset)
            dyn_dataset.data.data_format = DataFormat('DYNAMODB_TABLE', RowFormat.NONE, 0)
            dyn_dataset.data.compression = Compression.NONE
            dyn_dataset.data.columns = [Column(c.name, dynamodb_column_type(c)) for c in dataset.data.columns]
            set_hive_vars = 'SET dynamodb.retry.duration = 0;\nSET dynamodb.throughput.write.percent = %s;'
            set_hive_vars = set_hive_vars % args_by_name['write_capacity_utilization_percent']

            i = add_to(step_funcs, i, hive_table_definition_step, stage_table_name, dataset, s3_step_path, local_step_path, action_id, False)
            i = add_to(step_funcs, i, hive_table_definition_step, target_table_name, dyn_dataset, s3_step_path, local_step_path, action_id, True)
            i = add_to(step_funcs, i, hive_msck_repair_table_step, stage_table_name, s3_step_path, action_id)
            i = add_to(step_funcs, i, hive_copy_to_table, dataset, stage_table_name, dyn_dataset, target_table_name, s3_step_path, local_step_path, action_id, set_hive_vars)

        # ------------------------------------------------------------------------------------------------------------
        # if no stage tables are needed, much complexity can be skipped
        # ------------------------------------------------------------------------------------------------------------
        elif staging_not_needed:
            i = add_to(step_funcs, i, hive_table_definition_step, target_table_name, dataset, s3_step_path, local_step_path, action_id, False)
            i = add_to(step_funcs, i, hive_msck_repair_table_step, target_table_name, s3_step_path, action_id)

        # ------------------------------------------------------------------------------------------------------------
        # one or more staging tables are needed
        # ------------------------------------------------------------------------------------------------------------
        else:
            stage_dataset = dataset
            target_dataset = Dataset.from_dict(dataset.to_dict())
            target_dataset.data.data_format = DataFormat(target_file_format, target_row_format, 0, target_delimited_by,
                                                         target_quoted_by, target_escaped_by, target_null_string)
            target_dataset.data.compression = target_compression
            drop_table_names.append(stage_table_name)

            # --------------------------------------------------------------------------------------------------------
            # define string types for JSON/REGEX based datasets (safe), and we will cast appropriately during insert
            # --------------------------------------------------------------------------------------------------------
            if stage_dataset.data.data_format.row_format in [RowFormat.JSON, RowFormat.REGEX]:
                # make a copy since we are modifying the columns
                stage_dataset = Dataset.from_dict(dataset.to_dict())
                assert isinstance(stage_dataset, Dataset)
                for c in stage_dataset.data.columns:
                    c.data_type = DataType.STRING

            i = add_to(step_funcs, i, hive_table_definition_step, stage_table_name, stage_dataset, s3_step_path, local_step_path, action_id, False)
            i = add_to(step_funcs, i, hive_table_definition_step, target_table_name, target_dataset, s3_step_path, local_step_path, action_id, False)
            i = add_to(step_funcs, i, hive_msck_repair_table_step, stage_table_name, s3_step_path, action_id)

            # --------------------------------------------------------------------------------------------------------
            # hive has issues creating parquet files
            # --------------------------------------------------------------------------------------------------------
            if target_file_format != FileFormat.PARQUET:
                i = add_to(step_funcs, i, hive_copy_to_table, stage_dataset, stage_table_name, target_dataset, target_table_name, s3_step_path, local_step_path, action_id, None)

            # --------------------------------------------------------------------------------------------------------
            # impala is better for creating parquet files
            # --------------------------------------------------------------------------------------------------------
            else:
                # ----------------------------------------------------------------------------------------------------
                # no additional staging tables needed if the source dataset file format is RCFILE (impala friendly)
                # ----------------------------------------------------------------------------------------------------
                if dataset.data.data_format.file_format == FileFormat.RCFILE:
                    i = add_to(step_funcs, i, hive_copy_to_table, stage_dataset, stage_table_name, target_dataset, target_table_name, s3_step_path, local_step_path, action_id, None)

                # ----------------------------------------------------------------------------------------------------
                # impala cannot read all hive formats, so we will introduce another staging table
                # ----------------------------------------------------------------------------------------------------
                else:
                    rc_table_name = target_table_name + '_rcfile_stage_for_action_' + action_id
                    rc_dataset = Dataset.from_dict(target_dataset.to_dict())
                    rc_dataset.data.data_format = DataFormat(FileFormat.RCFILE, RowFormat.NONE, 0)
                    rc_dataset.data.compression = Compression.NONE
                    drop_table_names.append(rc_table_name)

                    i = add_to(step_funcs, i, hive_table_definition_step, rc_table_name, rc_dataset, s3_step_path, local_step_path, action_id, False)
                    i = add_to(step_funcs, i, hive_copy_to_table, stage_dataset, stage_table_name, rc_dataset, rc_table_name, s3_step_path, local_step_path, action_id, None)
                    i = add_to(step_funcs, i, impala_copy_to_table, rc_dataset, rc_table_name, target_dataset, target_table_name, s3_step_path, local_step_path, action_id)

        # ------------------------------------------------------------------------------------------------------------
        # at this point, the load should be considered complete even if something goes wrong in the steps below,
        # so we will indicate this in the step wrapper
        # ------------------------------------------------------------------------------------------------------------
        considered_successful_at_this_index = i

        # ------------------------------------------------------------------------------------------------------------
        # drop any staging tables created
        # ------------------------------------------------------------------------------------------------------------
        if drop_table_names:
            script = '\n'.join(['DROP TABLE %s;' % name for name in drop_table_names])
            i = add_to(step_funcs, i, hive_run_script_contents_step, script, s3_step_path, local_step_path, action_id)

        # ------------------------------------------------------------------------------------------------------------
        # inform impala about changes
        # ------------------------------------------------------------------------------------------------------------
        if not target_is_dynamodb:
            i = add_to(step_funcs, i, impala_invalidate_metadata_step, s3_step_path, action_id)

        total_steps = i - 1
        steps = []
        for index, f in enumerate(step_funcs, 1):
            step_wrapper = f(total_steps)
            assert isinstance(step_wrapper, StepWrapper)
            if index >= considered_successful_at_this_index:
                step_wrapper.action_considered_successful = True
            steps.append(step_wrapper)

        if not dry_run:
            s3_copy_recursive(local_step_path, s3_step_path)

        return steps

    finally:
        shutil.rmtree(tempdir)


def load_dataset_s3_path_and_file_size_generator(emr_engine, action, dataset=None):
    if dataset is None:
        dataset = emr_engine.dart.get_dataset(action.data.args['dataset_id'])
    conn = boto.connect_s3()
    s3_keys = yield_s3_keys(
        get_bucket(conn, dataset.data.location),
        dataset.data.location,
        action.data.args.get('s3_path_start_prefix_inclusive'),
        action.data.args.get('s3_path_end_prefix_exclusive'),
        action.data.args.get('s3_path_regex_filter'),
        action.data.args.get('s3_path_start_prefix_inclusive_date_offset_in_seconds'),
        action.data.args.get('s3_path_end_prefix_exclusive_date_offset_in_seconds'),
        action.data.args.get('s3_path_regex_filter_date_offset_in_seconds'),
    )
    for key_obj in s3_keys:
        yield get_s3_path(key_obj), key_obj.size
