import logging
import os
import json
from abc import abstractmethod

from dart.model.engine import ActionResultState
from dart.tool.tool_runner import Tool

_logger = logging.getLogger(__name__)

class ActionRunner(Tool):
    def __init__(self, logger, configure_app_context=True):
        super(ActionRunner, self).__init__(logger, configure_app_context=False)
        _logger = logger

        # Env variable input_env is a json dump of all variables we need for batch processing.
        # It will include user_id, workflow_instance_id, workflow_id, datastore_id, sns_arn, is_continue_on_failure,
        # current_step_id (action template), output/input key (tmp files), ACTION_ID, is_first_action, is_last_action
        # E.g. [{"name": "user_id", "value": "bkennedy@rmn.com"}, {"name": "workflow_instance_id", "value": "3GLS4J1E74"}, {"name": "retries_on_failures", "value": "0"}, {"name": "workflow_id", "value": "2WEMVMSWDT"}, {"name": "datastore_id", "value": "7UEPVG3VH6"}, {"name": "sns_arn", "value": "arn_value"}, {"name": "is_continue_on_failure", "value": "True"}, {"name": "current_step_id", "value": "NB6FQVQX8C"}, {"name": "output_key", "value": "3GLS4J1E74_1.dat"}, {"name": "input_key", "value": "3GLS4J1E74_0.dat"}, {"name": "ACTION_ID", "value": "KKW2YZJ7F2"}, {"name": "is_first_action", "value": "True"}, {"name": "is_last_action", "value": "False"}]
        self.is_continue_on_failure = False  # return success status when failed.  To allow batch to continue to execute.
        self.is_last_action = False  # Is it the last action in the workflow (which means end of workflow instance)
        input_env_str = os.getenv('input_env')
        if input_env_str:
            try:
                input_env = self.parse_input_env(input_env_str)

                self.is_continue_on_failure = True  # TODO - self.extract_input_value(input_env, 'is_continue_on_failure', True)
                self.is_last_action = self.extract_input_value(input_env, 'is_last_action', True)
                self.workflow_instance_id = self.extract_input_value(input_env, 'workflow_instance_id', True)
                self.sns_arn = self.extract_input_value(input_env, 'sns_arn')
                self.client = boto3.client('sns')
            except Exception as err:
                _logger.error("input_env {0} could not be parsed. err={1}".format(input_env_str, err))
                # for now the additional input_env_var is not added to engines so we do not support raissing an error yet.
                ### TODO -- raise ValueError(str(err))

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

    def publish_sns_message(self, action_id, error_message, action_result_state):
        if os.getenv('input_env'):  # we should not be notifying if no input_env was provided.
            self.publish_sns_message(action_id, error_message, action_result_state, self.is_last_action,
                                     self.workflow_instance_id, self.client.publish, self.is_continue_on_failure)

    def publish_sns_message(self, action_id, error_message, action_result_state, is_last_action, workflow_instance_id,
                            sns_arn, sns_client_publish, is_continue_on_failure):
        """
        :param action_id: the dart action id (not batch job_id)
        :param error_message: if the action failed the error will be sent in this field.
        :param action_result_state:  FAILURE/SUCCESS
        :param is_last_action: last action in the workflow
        :param workflow_instance_id: the workflow instance this action is running at
        :param sns_arn: Where to send the action complete (FAILED/SUCCEEDED) message to be processesed by lambdas
        :param sns_client_publish: boto3 client (sent in order to simplify testing with mocks).
        :param is_continue_on_failure: whether to raise an exception and end the docker action execution with failure or not if the action actually fails.
               Need for batch processing that stops all dependent jobs if one fails.
        :return: Message sent but raises an error if action failed and we are not marked to continue of failure.

        >>> cls.publish_sns_message(12, "error", ActionResultState.SUCCESS, True, "222", "arn-123", sns_publish_success, False)['status']
        'SUCCEEDED'

        >>> cls.publish_sns_message(12, "error", ActionResultState.SUCCESS, True, "222", "arn-123", sns_publish_success, False)['action_id']
        '12'

        >>> cls.publish_sns_message(12, "error", ActionResultState.SUCCESS, True, "222", "arn-123", sns_publish_success, False)['workflow_instance_id']
        '222'

        >>> cls.publish_sns_message(12, "error", ActionResultState.SUCCESS, False, "222", "arn-123", sns_publish_success, True)
        {'status': 'SUCCEEDED', 'workflow_instance_id': '', 'error_message': 'error', 'source': 'Custom DART Action', 'action_id': '12'}

        >>> cls.publish_sns_message(12, "deliberate_error", ActionResultState.FAILURE, True, "222", "arn-123", sns_publish_success, False) # failed action without continue on failure
        Traceback (most recent call last):
        ...
        ValueError: deliberate_error

        >>> cls.publish_sns_message(12, "sns_error", ActionResultState.FAILURE, True, "222", "arn-123", sns_publish_failure, False)
        Traceback (most recent call last):
        ...
        ValueError: sns_error
        """
        sns_message = dict(action_id=str(action_id),
                           source="Custom DART Action",
                           error_message=error_message,
                           status="FAILED",
                           workflow_instance_id="")

        if action_result_state == ActionResultState.SUCCESS:
            sns_message["status"] = "SUCCEEDED"

        if is_last_action:
            sns_message["workflow_instance_id"] = str(workflow_instance_id)

        try:
            sns_client_publish(
                TargetArn=sns_arn,
                Message=json.dumps(json.dumps(sns_message)),
                MessageStructure='json'
            )
        except Exception as err:
            _logger.error("Could not notify sns {0} with message {1}. err={2}".format(sns_arn, error_message, err))

        if (action_result_state == ActionResultState.FAILURE) and (not is_continue_on_failure):
            raise ValueError(error_message)

        return sns_message

    @abstractmethod
    def run(self):
        raise NotImplementedError


if __name__ == "__main__":
    import doctest


    def sns_publish_success(TargetArn, Message, MessageStructure='json'):
        return {}

    def sns_publish_failure(TargetArn, Message, MessageStructure='json'):
        raise ValueError("Failed_SNS")

    logging.basicConfig()
    log = logging.getLogger('Test_Action_Runner')

    doctest.testmod(extraglobs={'cls': ActionRunner(log, False),
                                'sns_publish_success': sns_publish_success,
                                'sns_publish_failure': sns_publish_failure})