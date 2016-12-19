# must run pip install -e . in src/python folder before running this unit test
import unittest

from dart.auth.rmn_required_roles_impl import prepare_inputs, authorization_decorator


class InputTests(unittest.TestCase):

    class User(object):
        email = ""
        def __init__(self, email):
            self.email = email

        def __str__(self):
            return self.email

    def setUp(self):
        user = self.User('dart@rmn.com')
        self.inputs = { 'current_user': user,
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