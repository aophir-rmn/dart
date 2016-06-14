import unittest

from dart.client.python.dart_client import Dart
from dart.engine.no_op.metadata import NoOpActionTypes
from dart.model.action import ActionData, Action, ActionState
from dart.model.dataset import Column, DataFormat, FileFormat, RowFormat, DatasetData, Dataset
from dart.model.dataset import DataType, LoadType
from dart.model.datastore import Datastore, DatastoreData, DatastoreState
from dart.model.event import Event, EventState
from dart.model.event import EventData
from dart.model.subscription import Subscription
from dart.model.subscription import SubscriptionData
from dart.model.trigger import Trigger, TriggerState
from dart.model.trigger import TriggerData
from dart.model.workflow import WorkflowData, WorkflowState
from dart.model.workflow import Workflow
from dart.util.rand import random_id


class TestEntityGraph(unittest.TestCase):
    def setUp(self):
        dart = Dart(host='localhost', port=5000)
        """ :type dart: dart.client.python.dart_client.Dart """
        self.dart = dart

        cs = [Column('c1', DataType.VARCHAR, 50), Column('c2', DataType.BIGINT)]
        df = DataFormat(FileFormat.PARQUET, RowFormat.NONE)
        dataset_data = DatasetData(name='test-dataset0',
                                   table_name='test_dataset_table0',
                                   load_type=LoadType.INSERT,
                                   location=('s3://test/dataset/0/%s' + random_id()),
                                   data_format=df,
                                   columns=cs,
                                   tags=[])
        self.dataset0 = self.dart.save_dataset(Dataset(data=dataset_data))

        cs = [Column('c1', DataType.VARCHAR, 50), Column('c2', DataType.BIGINT)]
        df = DataFormat(FileFormat.PARQUET, RowFormat.NONE)
        dataset1_location = 's3://test/dataset/1/%s' + random_id()
        dataset_data = DatasetData(name='test-dataset1',
                                   table_name='test_dataset_table1',
                                   load_type=LoadType.INSERT,
                                   location=dataset1_location,
                                   data_format=df,
                                   columns=cs,
                                   tags=[])
        self.dataset1 = self.dart.save_dataset(Dataset(data=dataset_data))

        cs = [Column('c1', DataType.VARCHAR, 50), Column('c2', DataType.BIGINT)]
        df = DataFormat(FileFormat.PARQUET, RowFormat.NONE)
        dataset_data = DatasetData(name='test-dataset2-no-show',
                                   table_name='test_dataset_table2',
                                   load_type=LoadType.INSERT,
                                   location=('s3://test/dataset/2/%s' + random_id()),
                                   data_format=df,
                                   columns=cs,
                                   tags=[])
        self.dataset2 = self.dart.save_dataset(Dataset(data=dataset_data))

        s = Subscription(data=SubscriptionData('test-subscription0', self.dataset0.id))
        self.subscription0 = self.dart.save_subscription(s)

        s = Subscription(data=SubscriptionData('test-subscription2-no-show', self.dataset2.id))
        self.subscription2 = self.dart.save_subscription(s)

        dst_args = {'action_sleep_time_in_seconds': 0}
        dst = Datastore(data=DatastoreData('test-datastore0', 'no_op_engine', args=dst_args, state=DatastoreState.TEMPLATE))
        self.datastore0 = self.dart.save_datastore(dst)
        dst = Datastore(data=DatastoreData('test-datastore1', 'no_op_engine', args=dst_args, state=DatastoreState.TEMPLATE))
        self.datastore1 = self.dart.save_datastore(dst)
        dst = Datastore(data=DatastoreData('test-datastore2-no-show', 'no_op_engine', args=dst_args, state=DatastoreState.ACTIVE))
        self.datastore2 = self.dart.save_datastore(dst)

        wf0 = Workflow(data=WorkflowData('test-workflow0', self.datastore0.id, state=WorkflowState.ACTIVE))
        self.workflow0 = self.dart.save_workflow(wf0, self.datastore0.id)
        wf1 = Workflow(data=WorkflowData('test-workflow1', self.datastore1.id, state=WorkflowState.ACTIVE))
        self.workflow1 = self.dart.save_workflow(wf1, self.datastore1.id)
        wf2 = Workflow(data=WorkflowData('test-workflow2-no-show', self.datastore2.id, state=WorkflowState.ACTIVE))
        self.workflow2 = self.dart.save_workflow(wf2, self.datastore2.id)

        a_args = {'source_hdfs_path': 'hdfs:///user/hive/warehouse/test', 'destination_s3_path': dataset1_location}
        a00 = Action(data=ActionData(NoOpActionTypes.action_that_succeeds.name, NoOpActionTypes.action_that_succeeds.name, state=ActionState.TEMPLATE))
        a01 = Action(data=ActionData(NoOpActionTypes.consume_subscription.name, NoOpActionTypes.consume_subscription.name, {'subscription_id': self.subscription0.id}, state=ActionState.TEMPLATE))
        a02 = Action(data=ActionData(NoOpActionTypes.action_that_succeeds.name, NoOpActionTypes.action_that_succeeds.name, state=ActionState.TEMPLATE))
        a03 = Action(data=ActionData(NoOpActionTypes.copy_hdfs_to_s3_action.name, NoOpActionTypes.copy_hdfs_to_s3_action.name, a_args, state=ActionState.TEMPLATE))
        a04 = Action(data=ActionData(NoOpActionTypes.action_that_succeeds.name, NoOpActionTypes.action_that_succeeds.name, state=ActionState.TEMPLATE))
        self.action00, self.action01, self.action02, self.action03, self.action04 = \
            self.dart.save_actions([a00, a01, a02, a03, a04], workflow_id=self.workflow0.id)

        a10 = Action(data=ActionData(NoOpActionTypes.load_dataset.name, NoOpActionTypes.load_dataset.name, {'dataset_id': self.dataset1.id}, state=ActionState.TEMPLATE))
        self.action10 = self.dart.save_actions([a10], workflow_id=self.workflow1.id)

        a20 = Action(data=ActionData(NoOpActionTypes.action_that_succeeds.name, NoOpActionTypes.action_that_succeeds.name, state=ActionState.HAS_NEVER_RUN))
        a21 = Action(data=ActionData(NoOpActionTypes.load_dataset.name, NoOpActionTypes.load_dataset.name, {'dataset_id': self.dataset2.id}, state=ActionState.TEMPLATE))
        self.action20 = self.dart.save_actions([a20], datastore_id=self.datastore2.id)
        self.action21 = self.dart.save_actions([a21], workflow_id=self.workflow2.id)

        self.event1 = self.dart.save_event(Event(data=EventData('test-event1', state=EventState.ACTIVE)))
        self.event2 = self.dart.save_event(Event(data=EventData('test-event2-no-show', state=EventState.ACTIVE)))

        tr_args = {'event_id': self.event1.id}
        tr = Trigger(data=TriggerData('test-event-trigger1', 'event', [self.workflow1.id], tr_args, TriggerState.ACTIVE))
        self.event_trigger1 = self.dart.save_trigger(tr)

        tr_args = {'event_id': self.event2.id}
        tr = Trigger(data=TriggerData('test-event-trigger2-no-show', 'event', [self.workflow2.id], tr_args, TriggerState.ACTIVE))
        self.event_trigger2 = self.dart.save_trigger(tr)

        tr_args = {'completed_workflow_id': self.workflow0.id}
        tr = Trigger(data=TriggerData('test-workflow-trigger', 'workflow_completion', None, tr_args, TriggerState.ACTIVE))
        self.wf_trigger = self.dart.save_trigger(tr)

        st_args = {'fire_after': 'ALL', 'completed_trigger_ids': [self.wf_trigger.id, self.event_trigger1.id]}
        st = Trigger(data=TriggerData('test-super-trigger1', 'super', None, st_args, TriggerState.ACTIVE))
        self.super_trigger1 = self.dart.save_trigger(st)

        st_args = {'fire_after': 'ANY', 'completed_trigger_ids': [self.super_trigger1.id]}
        st = Trigger(data=TriggerData('test-super-trigger2', 'super', [self.workflow1.id], st_args, TriggerState.ACTIVE))
        self.super_trigger2 = self.dart.save_trigger(st)

    def tearDown(self):
        for a in self.dart.get_actions(workflow_id=self.workflow0.id):
            self.dart.delete_action(a.id)
        for a in self.dart.get_actions(workflow_id=self.workflow1.id):
            self.dart.delete_action(a.id)
        self.dart.delete_trigger(self.super_trigger2.id)
        self.dart.delete_trigger(self.super_trigger1.id)
        self.dart.delete_trigger(self.wf_trigger.id)
        self.dart.delete_trigger(self.event_trigger1.id)
        self.dart.delete_trigger(self.event_trigger2.id)
        self.dart.delete_event(self.event1.id)
        self.dart.delete_event(self.event2.id)
        self.dart.delete_workflow(self.workflow0.id)
        self.dart.delete_workflow(self.workflow1.id)
        self.dart.delete_workflow(self.workflow2.id)
        self.dart.delete_datastore(self.datastore0.id)
        self.dart.delete_datastore(self.datastore1.id)
        self.dart.delete_datastore(self.datastore2.id)
        self.dart.delete_subscription(self.subscription0.id)
        self.dart.delete_subscription(self.subscription2.id)
        self.dart.delete_dataset(self.dataset0.id)
        self.dart.delete_dataset(self.dataset1.id)
        self.dart.delete_dataset(self.dataset2.id)

    def test_entity_graph(self):
        graph_entities = self.dart.get_entity_graph('dataset', self.dataset0.id)
        for e in graph_entities.nodes:
            self.assertNotRegexpMatches(e.name, '-no-show')


if __name__ == '__main__':
    unittest.main()
