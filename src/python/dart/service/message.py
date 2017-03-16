import os
from boto.ec2containerservice.layer1 import EC2ContainerServiceConnection
from boto.regioninfo import RegionInfo
from sqlalchemy import text
from dart.model.orm import MessageDao
from dart.context.database import db
from dart.service.patcher import patch_difference


class MessageService(object):
    def __init__(self, ecs_task_status_override=None, region='us-east-1'):
        self._ecs_task_status_override = ecs_task_status_override
        self._region = RegionInfo(self, region, 'ecs.%s.amazonaws.com' % region) if region else None
        self._conn = None

    @staticmethod
    def save_message(message_id, message_body, state):
        message_dao = MessageDao()
        message_dao.id = message_id
        message_dao.message_body = message_body
        message_dao.instance_id = os.environ['DART_INSTANCE_ID']
        message_dao.container_id = os.environ['DART_CONTAINER_ID']
        message_dao.ecs_cluster = os.environ['DART_ECS_CLUSTER']
        message_dao.ecs_container_instance_arn = os.environ['DART_ECS_CONTAINER_INSTANCE_ARN']
        message_dao.ecs_family = os.environ['DART_ECS_FAMILY']
        message_dao.ecs_task_arn = os.environ['DART_ECS_TASK_ARN']
        message_dao.state = state
        db.session.add(message_dao)
        db.session.commit()
        return message_dao.to_model()

    def get_ecs_task_status(self, message):
        """ :type message: dart.model.message.Message """
        if self._ecs_task_status_override:
            if self._ecs_task_status_override == 'passthrough':
                return 'RUNNING' if message.state == 'RUNNING' else 'STOPPED'
            return self._ecs_task_status_override

        return self.get_ecs_task_status_direct(message.ecs_task_arn, message.ecs_cluster)

    # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_life_cycle.html
    def get_ecs_task_status_direct(self, ecs_task_arn, ecs_cluster):
        result = self.conn.describe_tasks([ecs_task_arn], ecs_cluster)
        tasks = result['DescribeTasksResponse']['DescribeTasksResult']['tasks']
        if len(tasks) == 0:
            return None
        return tasks[0]['desiredStatus']

    @staticmethod
    def get_message(message_id, raise_when_missing=True):
        message_dao = MessageDao.query.get(message_id)
        if not message_dao and raise_when_missing:
            raise Exception('message with id=%s not found' % message_id)
        return message_dao.to_model() if message_dao else None

    @staticmethod
    def update_message_state(message, state):
        """ :type message: dart.model.message.Message """
        source_message = message.copy()
        message.state = state
        return patch_difference(MessageDao, source_message, message)

    @staticmethod
    def purge_old_messages():
        db.session.execute(text(""" DELETE FROM message WHERE created <  (NOW() - INTERVAL '5 days') """))
        db.session.commit()

    @property
    def conn(self):
        if self._conn:
            return self._conn
        self._conn = EC2ContainerServiceConnection(region=self._region)
        return self._conn
