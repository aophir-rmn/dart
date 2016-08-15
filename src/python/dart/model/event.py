from dart.model.base import BaseModel, dictable


class EventState(object):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

    @staticmethod
    def all():
        return [EventState.ACTIVE, EventState.INACTIVE]


@dictable
class Event(BaseModel):
    def __init__(self, id=None, version_id=None, created=None, updated=None, data=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type data: dart.model.event.EventData
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.data = data


@dictable
class EventData(BaseModel):
    def __init__(self, name, description=None, state=EventState.INACTIVE, tags=None, user_id='anonymous'):
        """
        :type name: str
        :type description: str
        :type state: str
        :type tags: list[str]
        """
        self.name = name
        self.description = description
        self.state = state
        self.tags = tags or []
        self.user_id = user_id
