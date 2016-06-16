import os
import unittest

from dart.client.python.dart_client import Dart
from dart.engine.no_op.metadata import NoOpActionTypes
from dart.model.action import ActionData, Action, ActionState
from dart.model.dataset import Column, DatasetData, Dataset, DataFormat, DataType, FileFormat, RowFormat, LoadType
from dart.model.datastore import Datastore, DatastoreData, DatastoreState
from dart.model.subscription import Subscription, SubscriptionData, SubscriptionElementStats, SubscriptionElementState, \
    SubscriptionState
from dart.model.trigger import Trigger, TriggerState
from dart.model.trigger import TriggerData
from dart.model.workflow import WorkflowData, WorkflowState, WorkflowInstanceState
from dart.model.workflow import Workflow


class TestConsumeSubscription(unittest.TestCase):
    def setUp(self):
        dart = Dart(host='localhost', port=5000)
        """ :type dart: dart.client.python.dart_client.Dart """
        self.dart = dart

        cs = [Column('c1', DataType.VARCHAR, 50), Column('c2', DataType.BIGINT)]
        df = DataFormat(FileFormat.TEXTFILE, RowFormat.DELIMITED)
        dataset_data = DatasetData(name='test-dataset', table_name='test_dataset_table',
                                   load_type=LoadType.INSERT,
                                   location=('s3://' + os.environ['DART_TEST_BUCKET'] + '/impala'),
                                   data_format=df,
                                   columns=cs,
                                   tags=[])
        self.dataset = self.dart.save_dataset(Dataset(data=dataset_data))

        start = 's3://' + os.environ['DART_TEST_BUCKET'] + '/impala/impala'
        end = 's3://' + os.environ['DART_TEST_BUCKET'] + '/impala/install'
        regex = '.*\\.rpm'
        ds = Subscription(data=SubscriptionData('test-subscription', self.dataset.id, start, end, regex))
        self.subscription = self.dart.save_subscription(ds)

        dst_args = {'action_sleep_time_in_seconds': 0}
        dst = Datastore(data=DatastoreData('test-datastore', 'no_op_engine', args=dst_args, state=DatastoreState.TEMPLATE))
        self.datastore = self.dart.save_datastore(dst)

        wf = Workflow(data=WorkflowData('test-workflow', self.datastore.id, state=WorkflowState.ACTIVE))
        self.workflow = self.dart.save_workflow(wf, self.datastore.id)

        a_args = {'subscription_id': self.subscription.id}
        a0 = Action(data=ActionData(NoOpActionTypes.action_that_succeeds.name, NoOpActionTypes.action_that_succeeds.name, state=ActionState.TEMPLATE))
        a1 = Action(data=ActionData(NoOpActionTypes.consume_subscription.name, NoOpActionTypes.consume_subscription.name, a_args, state=ActionState.TEMPLATE))
        self.action0, self.action1 = self.dart.save_actions([a0, a1], workflow_id=self.workflow.id)

    def tearDown(self):
        for a in self.dart.get_actions(workflow_id=self.workflow.id):
            self.dart.delete_action(a.id)
        for wfi in self.dart.get_workflow_instances(self.workflow.id):
            self.dart.delete_datastore(wfi.data.datastore_id)
        self.dart.delete_workflow_instances(self.workflow.id)
        self.dart.delete_workflow(self.workflow.id)
        self.dart.delete_datastore(self.datastore.id)
        self.dart.delete_subscription(self.subscription.id)
        self.dart.delete_dataset(self.dataset.id)

    def test_consume_subscription(self):
        subscription = self.dart.await_subscription_generation(self.subscription.id)
        self.assertEqual(subscription.data.state, SubscriptionState.ACTIVE)

        tr_args = {'subscription_id': self.subscription.id, 'unconsumed_data_size_in_bytes': 49524}
        tr = Trigger(data=TriggerData('test-trigger', 'subscription_batch', [self.workflow.id], tr_args, TriggerState.ACTIVE))
        self.trigger = self.dart.save_trigger(tr)

        wf_instances = self.dart.await_workflow_completion(self.workflow.id, num_instances=3)
        for wfi in wf_instances:
            self.assertEqual(wfi.data.state, WorkflowInstanceState.COMPLETED)

        stats = self.dart.get_subscription_element_stats(self.subscription.id)
        ses = SubscriptionElementStats(SubscriptionElementState.CONSUMED, 3, 152875004 + 834620 + 49524)
        self.assertEqual([s.to_dict() for s in stats], [ses.to_dict()])

        self.dart.delete_trigger(self.trigger.id)

if __name__ == '__main__':
    unittest.main()
