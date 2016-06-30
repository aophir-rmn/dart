from dart.model.base import dictable, BaseModel


@dictable
class TriggerType(BaseModel):
    def __init__(self, name, description=None, params_json_schema=None):
        """
        :type name: str
        :type description: str
        :type params_json_schema: dict
        """
        self.name = name
        self.description = description
        self.params_json_schema = params_json_schema


class TriggerState(object):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

    @staticmethod
    def all():
        return [TriggerState.ACTIVE, TriggerState.INACTIVE]


@dictable
class Trigger(BaseModel):
    def __init__(self, id=None, version_id=None, created=None, updated=None, data=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type data: dart.model.trigger.TriggerData
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.data = data


@dictable
class TriggerData(BaseModel):
    def __init__(self, name, trigger_type_name, workflow_ids=None, args=None, state=TriggerState.INACTIVE,
                 extra_data=None, tags=None, user_id='anonymous'):
        """
        :type name: str
        :type trigger_type_name: str
        :type workflow_ids: list[str]
        :type args: dict
        :type state: str
        :type tags: list[str]
        :type extra_data: dict
        """
        self.trigger_type_name = trigger_type_name
        self.name = name
        self.workflow_ids = workflow_ids
        self.tags = tags or []
        self.args = args
        self.state = state
        self.extra_data = extra_data
        self.user_id = user_id
