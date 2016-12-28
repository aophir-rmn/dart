# must run pip install -e . in src/python folder before running this unit test
import unittest
from collections import namedtuple

from dart.auth.rmn_required_roles_impl import prepare_inputs, authorization_decorator, does_key_exist


class InputTests(unittest.TestCase):

    # This function creates a fake user_role_Service object. It returns values (action_list and membership_list) only
    # for the recognized_user, otherwise it throws and error.
    # e.g action_list=['Can_edit'], membership_list=['Is_member_Of_BA']
    def create_fake_user_role_service(self, recognized_user, action_list, membership_list):
        def get_user_roles_func(usr):
            if usr == recognized_user:
                return action_list, membership_list

            raise ValueError("wrong user")

        FakeUserRoles = namedtuple('FakeUserRoles', 'get_user_roles')
        return FakeUserRoles(get_user_roles=get_user_roles_func)

    def create_fake_kwargs(self, data=None, type='action'):
        def get_func(action_type):
            if (type == action_type):
                FakeData = namedtuple('FakeData', 'data')
                return FakeData(data=data)

            return None

        FakeKwargs = namedtuple('FakeKwargs', 'get')
        return FakeKwargs(get=get_func)

    def create_fake_get_known_entity(self, data=None):
        def get_known_entity_func(entity_name, id):
            FakeKnownEntity = namedtuple('FakeKnownEntity', 'data')
            return FakeKnownEntity(data=data)

        #get_known_entity,  data.datastore_id
        return get_known_entity_func

    class User(object):
        email = ""
        def __init__(self, email):
            self.email = email

        def __str__(self):
            return self.email

    def setUp(self):
        user = self.User('dart@rmn.com')
        self.inputs = {'current_user': user,
                       'kwargs': None,
                       'user_roles_service': None,
                       'get_known_entity': None,
                       'debug_uuid': 'DBG',
                       'action_roles': ['Edit'],
                       'dart_client_name': None
                       }

    def test_no_user(self):
        self.inputs['current_user'] = {}
        self.assertEqual(prepare_inputs(**self.inputs),
                         "Authorization: Cannot authorize user without email. user={}, action_roles=['Edit']")

    def test_wrong_action_roles(self):
        self.inputs['action_roles'] = ['typo']
        self.assertEqual(prepare_inputs(**self.inputs),
                         "Authorization: dart@rmn.com-DBG  Missing action_roles, not in ActionRoles ['Create', 'Edit', 'Run', 'Delete']. user=dart@rmn.com, action_roles=['typo']")

    def test_using_super_user(self):
        self.inputs['dart_client_name'] = self.inputs['current_user'].email
        ret = prepare_inputs(**self.inputs)
        self.assertTrue(isinstance(ret, dict))

    def test_using_user_with_Admin_membership(self):
        self.inputs['dart_client_name'] = 'whatever@rmn.com'
        self.inputs['user_roles_service'] = self.create_fake_user_role_service(self.inputs['current_user'].email,
                                                                               ['Can_Edit'],
                                                                               ['Is_Member_Of_BA', 'Is_Member_Of_Admin'])
        ret = prepare_inputs(**self.inputs)
        self.assertTrue(isinstance(ret, dict))

    def test_using_non_existing_user(self):
        self.inputs['dart_client_name'] = 'whatever@rmn.com'
        self.inputs['user_roles_service'] = self.create_fake_user_role_service("missing_user@rmn.com",
                                                                               ['Can_Edit'],
                                                                               ['Is_Member_Of_BA'])
        ret = prepare_inputs(**self.inputs)
        self.assertEqual(ret, "Authorization: dart@rmn.com-DBG  Current user's dart@rmn.com is likely not in database.")

    def test_using_user_with__non_Admin_membership(self):
        self.inputs['dart_client_name'] = 'whatever@rmn.com'
        self.inputs['user_roles_service'] = self.create_fake_user_role_service(self.inputs['current_user'].email,
                                                                               ['Can_Edit'],
                                                                               ['Is_Member_Of_BA'])
        FakeDatastoreId = namedtuple('FakeDatastoreId', 'datastore_id')
        fakeDatastoreId = FakeDatastoreId(datastore_id=self.inputs['current_user'].email)
        self.inputs['kwargs'] = self.create_fake_kwargs(data=fakeDatastoreId, type='workflow')

        FakeUserId = namedtuple('FakeDatastoreId', 'user_id')
        fakeUserId = FakeUserId(user_id=self.inputs['current_user'].email)
        self.inputs['get_known_entity'] = self.create_fake_get_known_entity(data=fakeUserId)

        ret = prepare_inputs(**self.inputs)
        self.assertTrue(isinstance(ret, dict))

    def test_using_non_existing_user(self):
        self.inputs['dart_client_name'] = 'whatever@rmn.com'
        self.inputs['user_roles_service'] = self.create_fake_user_role_service("missing_user@rmn.com",
                                                                               ['Can_Edit'],
                                                                               ['Is_Member_Of_BA'])
        ret = prepare_inputs(**self.inputs)
        self.assertEqual(ret, "Authorization: dart@rmn.com-DBG  Current user's dart@rmn.com is likely not in database.")

    def test_template_action_with_no_datastore_id(self):
        self.inputs['dart_client_name'] = 'whatever@rmn.com'
        self.inputs['user_roles_service'] = self.create_fake_user_role_service(self.inputs['current_user'].email,
                                                                               ['Can_Edit'],
                                                                               ['Is_Member_Of_BA'])

        FakeUserIdWithEmptyDatastoreId = namedtuple('FakeUserIdWithEmptyDatastoreId', ['user_id', 'datastore_id'])
        fakeUserIdWithEmptyDatastoreId = FakeUserIdWithEmptyDatastoreId(user_id=self.inputs['current_user'].email,
                                                                        datastore_id=u'')

        self.inputs['kwargs'] = self.create_fake_kwargs(data=fakeUserIdWithEmptyDatastoreId, type='action')
        self.inputs['get_known_entity'] = self.create_fake_get_known_entity(data=fakeUserIdWithEmptyDatastoreId)

        ret = prepare_inputs(**self.inputs)
        self.assertTrue(isinstance(ret, dict))

    def test_empty_datastoreid_key_does_not_exist(self):
        FakeUserIdWithEmptyDatastoreId = namedtuple('FakeUserIdWithEmptyDatastoreId', ['user_id', 'datastore_id'])
        fakeUserIdWithEmptyDatastoreId = FakeUserIdWithEmptyDatastoreId(user_id='whatever@rmn.com', datastore_id=u'')
        kwargs_empty_datastore_id = self.create_fake_kwargs(data=fakeUserIdWithEmptyDatastoreId, type='action')

        self.assertFalse(does_key_exist(kwargs=kwargs_empty_datastore_id ,dart_type='action', id_type='datastore_id'))
        self.assertTrue(does_key_exist(kwargs=kwargs_empty_datastore_id ,dart_type='action', id_type='user_id'))

    def test_real_datastoreid_key_exist(self):
        FakeUserIdWithRealDatastoreId = namedtuple('FakeUserIdWithRealDatastoreId', ['user_id', 'datastore_id'])
        fakeUserIdWithRealDatastoreId = FakeUserIdWithRealDatastoreId(user_id='whatever@rmn.com', datastore_id=u'real!')
        kwargs_real_datastore_id = self.create_fake_kwargs(data=fakeUserIdWithRealDatastoreId, type='action')

        self.assertTrue(does_key_exist(kwargs=kwargs_real_datastore_id ,dart_type='action', id_type='datastore_id'))
        self.assertTrue(does_key_exist(kwargs=kwargs_real_datastore_id ,dart_type='action', id_type='user_id'))



#################################
class DecoratorTests(unittest.TestCase):

    def setUp(self):
        self.inputs = {'user_': 'dart@rmn.com',
                       'current_user_actions_': [],
                       'current_user_memberships_': [],
                       'datastore_user_id_': 'a@b.c',
                       'ds_memberships_': [],
                       'is_ds_member_all_': False,
                       'DEBUG_ID_': 'DBG',
                       'action_roles_': ['Edit'],
                       'dart_client_name_': ''}

    def test_superuser_skip_checks(self):
        self.inputs['dart_client_name_'] = self.inputs['user_']
        self.assertEqual(authorization_decorator(**self.inputs), None)

    def test_admin_skip_checks(self):
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_Admin']
        self.assertEqual(authorization_decorator(**self.inputs), None)

    def test_no_shared_memberships_return_error_message(self):
      self.assertEqual(authorization_decorator(**self.inputs),
                       """DBG Current user's dart@rmn.com memberships [] do not
overlap with datastore's user owner a@b.c meberships []""")

    def test_no_shared_memberships_because_user_has_no_memberships_return_error_message(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['is_ds_member_all_'] = True

        self.assertEqual(authorization_decorator(**self.inputs),
                         """DBG Current user's dart@rmn.com memberships [] do not
overlap with datastore's user owner a@b.c meberships ['Is_Member_Of_BA']""")


    def test_shared_memberships_of_user_with_all_action_roles(self):
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Edit', 'Can_Run', 'Can_Delete']
        self.inputs['is_ds_member_all_'] = True
        self.assertEqual(authorization_decorator(**self.inputs), None)

    def test_shared_memberships_with_all_action_roles(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA', 'Is_Member_Of_GiftCards']
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Edit', 'Can_Run', 'Can_Delete']
        self.assertEqual(authorization_decorator(**self.inputs), None)

    def test_shared_memberships_with_action_role_Run_match(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA', 'Is_Member_Of_GiftCards']
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Run', 'Can_Delete']

        self.inputs['action_roles_'] = ['Run']
        self.assertEqual(authorization_decorator(**self.inputs), None)

    def test_shared_memberships_with_action_role_Edit_Missing(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA', 'Is_Member_Of_GiftCards']
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Run', 'Can_Delete']

        self.inputs['action_roles_'] = ['Edit']
        self.assertEqual(authorization_decorator(**self.inputs),
                         "DBG group specific roles ['Can_Edit_BA'] not exisiting for user's permissions\n['Can_Create', 'Can_Run', 'Can_Delete']. user=dart@rmn.com, action_roles=['Edit']")


    def test_shared_memberships_with_group_action_role_Run_match(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA', 'Is_Member_Of_GiftCards']
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Run_BA', 'Can_Delete']

        self.inputs['action_roles_'] = ['Run']
        self.assertEqual(authorization_decorator(**self.inputs), None)


    def test_shared_memberships_with_wrong_group_action_role_Run_match(self):
        self.inputs['ds_memberships_'] = ['Is_Member_Of_BA', 'Is_Member_Of_GiftCards']
        self.inputs['current_user_memberships_'] = ['Is_Member_Of_BA']
        self.inputs['current_user_actions_'] = ['Can_Create', 'Can_Run_GiftCards', 'Can_Delete']

        self.inputs['action_roles_'] = ['Run']
        self.assertEqual(authorization_decorator(**self.inputs), "DBG group specific roles ['Can_Run_BA'] not exisiting for user's permissions\n['Can_Create', 'Can_Run_GiftCards', 'Can_Delete']. user=dart@rmn.com, action_roles=['Run']")
