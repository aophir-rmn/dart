import re
import time
from dart.model.exception import DartActionException


def run_steps(emr_engine, datastore, action, step_wrappers):
    """
    :type emr_engine: dart.engine.emr.emr.EmrEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    :type step_wrappers: list[dart.engine.emr.steps.StepWrapper]
    """
    for step_wrapper in step_wrappers:
        try:
            run_step(emr_engine, datastore, action, step_wrapper)
        except Exception as e:
            raise DartActionException(e.message, step_wrapper)


def run_step(emr_engine, datastore, action, step_wrapper):
    """
    :type emr_engine: dart.engine.emr.emr.EmrEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    :type step_wrapper: dart.engine.emr.steps.StepWrapper
    """
    cluster_id = datastore.data.extra_data['cluster_id']
    emr_engine.conn.add_jobflow_steps(cluster_id, step_wrapper.step)
    while True:
        time.sleep(30)
        # http://docs.aws.amazon.com/ElasticMapReduce/latest/DeveloperGuide/emr-steps.html
        step_state = _get_step_state(action, step_wrapper, emr_engine.conn.list_steps(cluster_id))
        if step_state == 'COMPLETED':
            progress = "%.2f" % round(float(step_wrapper.step_num) / float(step_wrapper.steps_total), 2)
            updated_action = emr_engine.dart.patch_action(action, progress=progress)

            # do this so callers see an in-place update of the action
            action.data = updated_action.data

            return
        elif step_state not in ['RUNNING', 'PENDING']:
            values = (action.id, step_wrapper.step_num, step_state)
            raise Exception('action (id=%s) failed on step %s with state: %s' % values)


def _get_step_state(action, step_wrapper, emr_steps_summary):
    for emr_step in emr_steps_summary.steps:
        m = re.search(r'\(action_id=(.+?),step_num=(.+?),steps_total=(.+?)\)', emr_step.name)
        if not m:
            continue
        action_id, step_num, steps_total = m.group(1), int(m.group(2)), int(m.group(3))
        if action_id != action.id or step_num != step_wrapper.step_num:
            continue
        return emr_step.status.state
