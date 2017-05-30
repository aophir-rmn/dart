from dart.model.base import BaseModel, dictable


@dictable
class Subscription(BaseModel):
    def __init__(self, id=None, version_id=None, created=None, updated=None, data=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type data: dart.model.subscription.SubscriptionData
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.data = data


class SubscriptionState(object):
    INACTIVE = 'INACTIVE'
    QUEUED = 'QUEUED'
    GENERATING = 'GENERATING'
    FAILED = 'FAILED'
    ACTIVE = 'ACTIVE'

    @staticmethod
    def all():
        return [SubscriptionState.INACTIVE, SubscriptionState.QUEUED, SubscriptionState.GENERATING,
                SubscriptionState.FAILED, SubscriptionState.ACTIVE]


@dictable
class SubscriptionData(BaseModel):
    def __init__(self, name, dataset_id, s3_path_start_prefix_inclusive=None, s3_path_end_prefix_exclusive=None,
                 s3_path_regex_filter=None, state=SubscriptionState.INACTIVE, queued_time=None, generating_time=None,
                 initial_active_time=None, failed_time=None, message_id=None, on_failure_email=None,
                 on_success_email=None, tags=None, user_id='anonymous', nudge_id=None):
        """
        :type name: str
        :type dataset_id: str
        :type s3_path_start_prefix_inclusive: str
        :type s3_path_end_prefix_exclusive: str
        :type s3_path_regex_filter: str
        :type state: str
        :type queued_time: datetime.datetime
        :type generating_time: datetime.datetime
        :type initial_active_time: datetime.datetime
        :type failed_time: datetime.datetime
        :type message_id: str
        :type on_failure_email: list[str]
        :type on_success_email: list[str]
        :type tags: list[str]
        """
        self.name = name
        self.dataset_id = dataset_id
        self.s3_path_start_prefix_inclusive = s3_path_start_prefix_inclusive
        self.s3_path_end_prefix_exclusive = s3_path_end_prefix_exclusive
        self.s3_path_regex_filter = s3_path_regex_filter
        self.state = state
        self.queued_time = queued_time
        self.generating_time = generating_time
        self.initial_active_time = initial_active_time
        self.failed_time = failed_time
        self.message_id = message_id
        self.on_failure_email = on_failure_email or []
        self.on_success_email = on_success_email or []
        self.tags = tags or []
        self.user_id = user_id
        self.nudge_id = nudge_id


class SubscriptionElementState(object):
    UNCONSUMED = 'UNCONSUMED'
    RESERVED = 'RESERVED'
    ASSIGNED = 'ASSIGNED'
    CONSUMED = 'CONSUMED'


@dictable
class SubscriptionElement(BaseModel):
    def __init__(self, id, version_id, created, updated, subscription_id, s3_path, file_size,
                 state=SubscriptionElementState.UNCONSUMED, action_id=None, batch_id=None, processed=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type subscription_id: str
        :type s3_path: str
        :type file_size: long
        :type state: str
        :type action_id: str
        :type batch_id: str
        :type processed: datetime.datetime
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.subscription_id = subscription_id
        self.s3_path = s3_path
        self.file_size = file_size
        self.state = state
        self.action_id = action_id
        self.batch_id = batch_id
        self.processed = processed

@dictable
class SubscriptionElementStats(BaseModel):
    def __init__(self, state, count, file_size_sum):
        """
        :type state: str
        :type count: int
        :type file_size_sum: long
        """
        self.state = state
        self.count = count
        self.file_size_sum = file_size_sum
