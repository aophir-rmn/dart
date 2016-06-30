from dart.model.base import BaseModel, dictable


@dictable
class Datastore(BaseModel):
    def __init__(self, id=None, version_id=None, created=None, updated=None, data=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type data: dart.model.datastore.DatastoreData
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.data = data


class DatastoreState(object):
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'
    DONE = 'DONE'
    TEMPLATE = 'TEMPLATE'

    @staticmethod
    def all():
        return [DatastoreState.INACTIVE, DatastoreState.ACTIVE, DatastoreState.DONE, DatastoreState.TEMPLATE]


@dictable
class DatastoreData(BaseModel):
    def __init__(self, name, engine_name=None, workflow_datastore_id=None, host=None, port=None, connection_url=None,
                 s3_artifacts_path=None, s3_logs_path=None, state=DatastoreState.INACTIVE, concurrency=1, args=None,
                 extra_data=None, tags=None, user_id='anonymous'):
        """
        :type name: str
        :type engine_name: str
        :type workflow_datastore_id: str
        :type host: str
        :type port: int
        :type connection_url: str
        :type s3_artifacts_path: str
        :type s3_logs_path: str
        :type state: str
        :type concurrency: int
        :type args: dict
        :type extra_data: dict
        :type tags: list[str]
        """
        self.name = name
        self.engine_name = engine_name
        self.workflow_datastore_id = workflow_datastore_id
        self.host = host
        self.port = port
        self.connection_url = connection_url
        self.s3_artifacts_path = s3_artifacts_path
        self.s3_logs_path = s3_logs_path
        self.state = state
        self.concurrency = concurrency
        self.args = args
        self.extra_data = extra_data
        self.tags = tags or []
        self.user_id = user_id
