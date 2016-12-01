import logging
import time

from termcolor import colored

from dart_manager.util import DartManagerError

logger = logging.getLogger(__name__)


class DartDeployment(object):

    def __init__(self):
        super(DartDeployment, self).__init__()

    def deploy(self, create_core):
        # bring up core stack if necessary
        if create_core:
            self._deploy_stack('Core')

        # wait for core to stabilize
        while True:
            stack_status = self.get_stack_status('Core')
            if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                break
            else:
                message = 'Waiting for Dart Core stack to stabilize -- current status: {}'
                print(message.format(colored(stack_status, 'red')))
            time.sleep(5)

        

        # bring up the environment stack
        self._deploy_stack('Env')

    def _deploy_stack(self, stack_type):
        stack_config = self.config['CloudformationStacks'][stack_type]
        if stack_config['Arn'] is not None:
            raise DartManagerError('Cannot deploy Dart {}: stack ARN defined in config file'.format(stack_type))

        print('Starting Dart {} stack creation'.format(stack_type))
        stack_config['Arn'] = self.cf.create_stack(
            StackName=stack_config['Name'],
            TemplateBody=self.get_template(stack_type),
        )

        while True:
            time.sleep(5)
            stack_status = self.get_stack_status(stack_type)
            if stack_status == 'CREATE_COMPLETE':
                break
            elif stack_status == 'CREATE_IN_PROGRESS':
                print('Waiting for Dart {} stack to fully deploy'.format(stack_type))
            elif stack_status == 'CREATE_FAILED':
                DartManagerError('Dart {} stack failed to deploy'.format(stack_type))
            else:
                print('Unexpected Dart {} stack status: {}'.format(stack_type, colored(stack_status, 'red')))

        cprint('Dart {} stack successfully deployed'.format(stack_type), 'green')

    def check_stack_stable(self, stack_type):
        stack_status = self.get_stack_status(stack_type)
        if stack_status in ['CREATE_COMPLETE']:
            print('Dart {} stack successfully deployed'.format(stack_type))
            return True
        elif stack_status == 'CREATE_IN_PROGRESS':
            print('Waiting for Dart {} stack to fully deploy'.format(stack_type))
        elif stack_status == 'CREATE_FAILED':
            DartManagerError('Dart {} stack failed to deploy', stack_type)
        else:
            print('Unexpected Dart {} stack status: {}'.format(stack_type, colored(stack_status, 'red')))
        return False

    def _wait_for_stack_to_stabilize(self, stack_type):
        while True:
            stack_status = self.get_stack_status('Core')
            if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                message = 'Waiting for Dart {} stack to stabilize -- current status: {}'
                print(message.format(stack_type, colored(stack_status, 'red')))
            else:
                break

    def get_stack_status(self, stack_type):
        return self.cf.describe_stacks(
            StackName=self.stack_config['CloudformationStacks'][stack_type]['Arn']
        )['Stacks']['StackStatus']
