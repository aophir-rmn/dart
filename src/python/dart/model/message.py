from dart.model.base import BaseModel, dictable


class MessageState(object):
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


@dictable
class Message(BaseModel):
    def __init__(self, id, version_id, created, updated, message_body, instance_id, container_id, ecs_cluster,
                 ecs_container_instance_arn, ecs_family, batch_job_id, state=MessageState.RUNNING, ecs_task_arn='Batch_place_holder'):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type message_body: str
        :type instance_id: str
        :type container_id: str
        :type ecs_cluster: str
        :type ecs_container_instance_arn: str
        :type ecs_family: str
        :type ecs_task_arn: str
        :type batch_job_id: str
        :type state: str
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.message_body = message_body
        self.instance_id = instance_id
        self.container_id = container_id
        self.ecs_cluster = ecs_cluster
        self.ecs_container_instance_arn = ecs_container_instance_arn
        self.ecs_family = ecs_family
        self.ecs_task_arn = ecs_task_arn
        self.batch_job_id = batch_job_id
        self.state = state
