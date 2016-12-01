import unittest
from test._mock_backport import Mock

from engine.emr import consume_subscription
from engine.emr import ActionFailedButConsumeSuccessfulException
from engine.emr import StepWrapper
from dart.model.action import Action, ActionData
from dart.model.datastore import Datastore
from dart.model.exception import DartActionException


class TestConsumeSubscriptionExceptions(unittest.TestCase):

    def test_consume_subscription_exceptions(self):
        a = Action(id='abc123', data=ActionData('a_name', 'a_name', workflow_instance_id='abc123', args={'subscription_id': 0}))
        d = Datastore(id='abc123')

        mock_engine = self.init_mocks(Mock(side_effect=Exception()))
        with self.assertRaises(Exception):
            consume_subscription(mock_engine, d, a)
        mock_engine.dart.patch_action.assert_not_called()

        mock_engine = self.init_mocks(Mock(side_effect=Exception()))
        with self.assertRaises(ActionFailedButConsumeSuccessfulException):
            consume_subscription(mock_engine, d, a, consume_successful=True)
        mock_engine.dart.patch_action.assert_not_called()

        mock_engine = self.init_mocks(Mock(side_effect=DartActionException('failed', StepWrapper(None, 0, 0, False))))
        with self.assertRaises(Exception):
            consume_subscription(mock_engine, d, a)
        mock_engine.dart.patch_action.assert_not_called()

        mock_engine = self.init_mocks(Mock(side_effect=DartActionException('failed', StepWrapper(None, 0, 0, True))))
        with self.assertRaises(ActionFailedButConsumeSuccessfulException):
            consume_subscription(mock_engine, d, a)
        mock_engine.dart.patch_action.assert_not_called()

    def init_mocks(self, get_subscription_mock):
        mock_engine = Mock()
        mock_engine.dart = Mock()
        mock_engine.dart.patch_action = Mock()
        mock_engine.dart.get_subscription = get_subscription_mock
        return mock_engine


if __name__ == '__main__':
    unittest.main()
