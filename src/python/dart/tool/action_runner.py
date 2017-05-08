import logging
import os
import json
import boto3
from dart.model.engine import ActionResultState

from dart.engine.redshift.admin.utils import lookup_credentials

_logger = logging.getLogger(__name__)

class ActionRunner(object):
    def __init__(self):

        # Env variable input_env is a json dump of all variables we need for batch processing.
        # It will include user_id, workflow_instance_id, workflow_id, datastore_id, sns_arn, is_continue_on_failure,
        # current_step_id (action template), output/input key (tmp files), ACTION_ID, is_first_action
        # E.g. [{"name": "user_id", "value": "bkennedy@rmn.com"}, {"name": "workflow_instance_id", "value": "3GLS4J1E74"}, {"name": "retries_on_failures", "value": "0"}, {"name": "workflow_id", "value": "2WEMVMSWDT"}, {"name": "datastore_id", "value": "7UEPVG3VH6"}, {"name": "sns_arn", "value": "arn_value"}, {"name": "is_continue_on_failure", "value": "True"}, {"name": "current_step_id", "value": "NB6FQVQX8C"}, {"name": "output_key", "value": "3GLS4J1E74_1.dat"}, {"name": "input_key", "value": "3GLS4J1E74_0.dat"}, {"name": "ACTION_ID", "value": "KKW2YZJ7F2"}, {"name": "is_first_action", "value": "True"}]
        self.is_continue_on_failure = False  # return success status when failed.  To allow batch to continue to execute.
        input_env_str = os.getenv('input_env')
        if input_env_str:
            try:
                input_env = self.parse_input_env(input_env_str)

                self.is_continue_on_failure = self.extract_input_value(input_env, 'is_continue_on_failure', True)
                self.is_last_action = self.extract_input_value(input_env, 'is_last_action', True)
                self.workflow_instance_id = self.extract_input_value(input_env, 'workflow_instance_id')
                self.sns_arn = self.extract_input_value(input_env, 'sns_arn')
                self.retries_on_failures = int(self.extract_input_value(input_env, 'retries_on_failures'))
                _logger.info("is_continue_on_failure={0},  wf_instance_id={1}, sns_arn={2}".
                             format(self.is_continue_on_failure, self.workflow_instance_id, self.sns_arn))
            except Exception as err:
                _logger.error("input_env {0} could not be parsed. err={1}".format(input_env_str, err))
                raise ValueError(str(err))
        else:
            _logger.warn("no 'input_env' env variable provided.")

    def parse_input_env(self, input_env_str):
        """
        :param input_env_str: a string of inputs of the form [{"name": name1, "value": value1} ...]
        :return: a dictionary of name:value from input_env_str

        >>> cls.parse_input_env('{}')
        {}

        >>> cls.parse_input_env('[{"name": "name1", "value": "mike"}]')
        {u'name1': u'mike'}

        >>> cls.parse_input_env('[{"name": "name1", "value": "mike"}, {"name": "name2", "value": "john"}]')
        {u'name2': u'john', u'name1': u'mike'}
        """
        input_env_arr = json.loads(input_env_str)

        # turn {"name": "user_id", "value": "rveltidi@rmn.com"} to dictionary
        return {x['name']: x['value'] for x in input_env_arr}

    def extract_input_value(self, input_env, field, is_bool_true=False):
        """
        :param input_env: dictionary of key/values from the input_env env variable (include many values needed for Batch)
        :param field: a field in input_env (must exist)
        :param is_bool_true: if the field value (always string) is expected to be a bool we compare it to "True"
        :return: the value of the key 'field'

        >>> cls.extract_input_value(dict(k1="val1", k2='True'), "k1")
        'val1'

        >>> cls.extract_input_value(dict(k1="val1", k2="True"), "k2", True)
        True

        >>> cls.extract_input_value(dict(k1="val1", k2="False"), "k2", True)
        False

        >>> cls.extract_input_value(dict(k1="val1", k2="val2"), "k3")
        Traceback (most recent call last):
        ...
        ValueError: k3 not found in input_env {'k2': 'val2', 'k1': 'val1'}

        """
        if input_env:
            if field in input_env.keys():
                if is_bool_true:
                    return input_env[field] == "True"
                else:
                    return input_env[field]

        raise ValueError("{0} not found in input_env {1}".format(field, input_env))

    def publish_sns_message(self, action, error_message, action_result_state):
        """
        In order for the boto3 client to work we need the aws keys, session and a region.
        In addition the batch instance we will run in will need sts assume role permission to publish to sns_arn.
        :param action:
        :param error_message:
        :param action_result_state: We expect ActionResultState.SUCCESS or ActionResultState.FAILURE
        :return: nothing.
        """
        if os.getenv('input_env'):  # we should not be notifying if no input_env was provided.
            sns_client = None
            aws_access_key_id = None
            try:
                os.environ["AWS_DEFAULT_REGION"] = "us-east-1"  # boto3 needs a defined region.
                aws_access_key_id, aws_secret_access_key, security_token = lookup_credentials(action)
                sns_client = boto3.client('sns',
                                          aws_access_key_id=aws_access_key_id,
                                          aws_secret_access_key=aws_secret_access_key,
                                          aws_session_token=security_token)
            except Exception as err:
                _logger.error("Could not create boto3 sns client with aws_access_key_id={0}, err={1}".format(aws_access_key_id, err))

            self.publish_message(action_id=action.id,
                                 error_message=error_message,
                                 action_result_state=action_result_state,
                                 sns_arn=self.sns_arn,
                                 sns_client_publish=sns_client.publish,
                                 is_continue_on_failure=self.is_continue_on_failure)

    @staticmethod
    def publish_message(action_id, error_message, action_result_state,
                        sns_arn, sns_client_publish, is_continue_on_failure):
        """
        :param action_id: the dart action id (not batch job_id)
        :param error_message: if the action failed the error will be sent in this field.
        :param action_result_state:  FAILURE/SUCCESS
        :param sns_arn: Where to send the action complete (FAILED/SUCCEEDED) message to be processesed by lambdas
        :param sns_client_publish: boto3 client publish function (sent in order to simplify testing with mocks).
        :param is_continue_on_failure: whether to raise an exception and end the docker action execution with failure or not if the action actually fails.
               Need for batch processing that stops all dependent jobs if one fails.
        :return: Message sent but raises an error if action failed and we are not marked to continue of failure.

        >>> from pprint import pprint
        >>> pprint(cls.publish_message(12, "error", ActionResultState.SUCCESS, "arn-123", sns_publish_success, False))
        {'action_id': '12',
         'action_status': 'SUCCEEDED',
         'error_message': 'error',
         'source': 'Custom DART Action',
         'workflow_instance_id': '',
         'workflow_instance_status': ''}


        >>> pprint(cls.publish_message(12, "error", ActionResultState.SUCCESS, "arn-123", sns_publish_success, True))
        {'action_id': '12',
         'action_status': 'SUCCEEDED',
         'error_message': 'error',
         'source': 'Custom DART Action',
         'workflow_instance_id': '',
         'workflow_instance_status': ''}

        >>> cls.publish_message(12, "deliberate_error", ActionResultState.FAILURE, "arn-123", sns_publish_success, False)
        Traceback (most recent call last):
        ...
        ValueError: deliberate_error

        >>> cls.publish_message(12, "sns_error", ActionResultState.FAILURE, "arn-123", sns_publish_failure, False)
        Traceback (most recent call last):
        ...
        ValueError: sns_error
        """

        # The message will go directly to the SQS queue so its format is the same as the message in lambda: dart-batch-stage-batchEventStreamHandler
        sns_message = {'action_status': "SUCCEEDED" if (action_result_state == ActionResultState.SUCCESS) else 'FAILED',
                       'action_id': str(action_id),
                       'error_message': error_message,
                       'workflow_instance_id': '',
                       'workflow_instance_status': '',
                       'source': "Custom DART Action"}

        # 1. Report the correct action status to DART.
        # The only time we report the state of this action as SUCCEEDED when it is actually FAILED is when
        # is_continue_on_failure == True, so this is the only time we need to update The action state against DART
        if (sns_message['action_status'] == 'SUCCEEDED') or ((sns_message['action_status'] == 'FAILED') and is_continue_on_failure):
            # The workflow is not failed on a failed action when is_continue_on_failure == True
            # Even a last action does not effect the workflow_instance status if is_continue_on_failure==True
            try:
                sns_client_publish(
                    TopicArn=sns_arn,
                    Message=json.dumps(json.dumps(sns_message))
                )
            except Exception as err:
                _logger.error("Could not notify sns {0} with message {1}. err={2}".format(sns_arn, error_message, err))

            _logger.info("Notifying SNS message - {0}".format(sns_message))

        # 2. Mark the action as Failed (if needed) against Batch.
        # We mark the action as failed (including all dependent jobs) if it is failed and we are not requested to
        # continue. Batch will stop the workflow execution (dependency failure) and lambda
        # dart-batch-stage-batchEventStreamHandler will start the flow that updates the workflow_instance as 'Failed'.
        if (action_result_state == ActionResultState.FAILURE) and (not is_continue_on_failure):
            _logger.info("Failing action {0}, state = {1}, continue_on_failure={2} ".format(action_id, sns_message['action_status'], is_continue_on_failure))
            raise ValueError(error_message)

        return sns_message

if __name__ == "__main__":
    import doctest


    def sns_publish_success(TargetArn, Message, MessageStructure='json'):
        return {}

    def sns_publish_failure(TargetArn, Message, MessageStructure='json'):
        raise ValueError("Failed_SNS")

    logging.basicConfig()
    log = logging.getLogger('Test_Action_Runner')

    doctest.testmod(extraglobs={'cls': ActionRunner(),
                                'sns_publish_success': sns_publish_success,
                                'sns_publish_failure': sns_publish_failure})
