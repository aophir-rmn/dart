from engine.emr import prepare_load_dataset_steps
from engine.emr import ActionFailedButConsumeSuccessfulException
from engine.emr import run_steps
from dart.model.exception import DartActionException


def consume_subscription(emr_engine, datastore, action, consume_successful=False):
    """
    Having "consume_successful" as parameter (compared to a local variable) is helpful for testing

    :type emr_engine: dart.engine.emr.emr.EmrEngine
    :type datastore: dart.model.datastore.Datastore
    :type action: dart.model.action.Action
    """
    try:
        subscription = emr_engine.dart.get_subscription(action.data.args['subscription_id'])
        dataset = emr_engine.dart.get_dataset(subscription.data.dataset_id)
        dry_run = datastore.data.args['dry_run']
        generator = subscription_s3_path_and_file_size_generator(emr_engine.dart, action.id)
        steps = prepare_load_dataset_steps(dry_run, action.data.args, datastore, dataset, action.id, generator)
        if dry_run:
            consume_successful = True
            emr_engine.dart.patch_action(action, progress=1, extra_data={'steps': [s.to_dict() for s in steps]})
            return

        run_steps(emr_engine, datastore, action, steps)
        consume_successful = True
        emr_engine.dart.patch_action(action, progress=1)

    except Exception as e:
        msg = 'The following error occurred, and the subscription elements have been reverted to UNCONSUMED:\n'\
              + e.message
        if isinstance(e, DartActionException):
            step_wrapper = e.data
            if step_wrapper.action_considered_successful:
                consume_successful = True
        if consume_successful:
            msg = 'Although the following error occurred, the important EMR steps completed successfully and the' \
                  + ' subscription elements have been marked as CONSUMED:\n' + e.message
            raise ActionFailedButConsumeSuccessfulException(msg)

        raise Exception(msg)


def subscription_s3_path_and_file_size_generator(dart, action_id):
    for element in dart.get_subscription_elements(action_id):
        yield element.s3_path, element.file_size
