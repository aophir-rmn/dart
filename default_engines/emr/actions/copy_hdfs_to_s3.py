import shutil
import tempfile

from dart.util.s3 import s3_copy_recursive

from engine.emr import prepare_step_paths, python_copy_hdfs_to_s3
from engine.emr import run_steps


def copy_hdfs_to_s3(emr_engine, datastore, action):
    """
    :type emr_engine: dart.engine.emr.emr.EmrEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """
    src = action.data.args['source_hdfs_path']
    dest = action.data.args['destination_s3_path']
    dry_run = datastore.data.args['dry_run']

    steps = prepare_run_impala_script_steps(dry_run, datastore, action, src, dest)

    if dry_run:
        emr_engine.dart.patch_action(action, progress=1, extra_data={'steps': [s.to_dict() for s in steps]})
        return

    run_steps(emr_engine, datastore, action, steps)
    emr_engine.dart.patch_action(action, progress=1)


def prepare_run_impala_script_steps(dry_run, datastore, action, src, dest):
    # some steps require producing a dataset specific file based on a template, so we will copy all to a tempdir
    tempdir = tempfile.mkdtemp()
    try:
        local_step_path, s3_step_path, s3_temp_path = prepare_step_paths(datastore, tempdir)
        steps = [python_copy_hdfs_to_s3(s3_step_path, src, dest, s3_temp_path, action.id, 1, 1)]

        if not dry_run:
            s3_copy_recursive(local_step_path, s3_step_path)

        return steps

    finally:
        shutil.rmtree(tempdir)
