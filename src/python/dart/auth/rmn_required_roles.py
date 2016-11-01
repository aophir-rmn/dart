""" The decorator to decide if an dart api can be executed by user.
Assumptions: Roles are either of type Member_of (e.g. datascience or ba)
             or action role (e.g. create, edit, run, delete)
             and such roles exist in permission service.
             E.g. Is_Member_Of_DataScience, Can_Edit ...
             (The Is_Member_Of is expected prefix as well as Can_...)

Note:  All permissions are tied to the datastore owner on which we operate.
       As such we need to retrieve the datastore owner (if applicable) and
       its group membership to compare to the current user group.
       -- anonymous/none user datastore is free for all to edit/run/delete
       -- anonymous current user cannot do anything but view.

    * No limit on creating datastores.
"""
import logging
import os
from dart.config.config import configuration

from flask_login import current_user
from flask import make_response, current_app
from dart.service.user_roles import UserRolesService
from dart.web.api.entity_lookup import get_known_entity
from functools import wraps

_logger = logging.getLogger(__name__)
config_path = os.environ['DART_CONFIG']
config = configuration(config_path)
DART_CLIENT_NAME = config['authorization']['dart_client_name']


def dart_required_roles(action_roles):
    class Dart_Context(object):
        DATASTORE = 'Datastore'
        WORKFLOW = 'Workflow'
        WORKFLOW_INSTANCE = 'Workflow_Instance'
        ACTION = 'Action'
        TRIGGER = 'Trigger'

        @staticmethod
        def all():
            return [Dart_Context.DATASTORE,
                    Dart_Context.WORKFLOW,
                    Dart_Context.WORKFLOW_INSTANCE,
                    Dart_Context.ACTION,
                    Dart_Context.TRIGGER]

    class ActionRoles(object):
        CREATE = 'Create'
        EDIT = 'Edit'
        RUN = 'Run'
        DELETE = 'Delete'

        @staticmethod
        def all():
            return [ActionRoles.CREATE,
                    ActionRoles.EDIT,
                    ActionRoles.RUN,
                    ActionRoles.DELETE]

    class RoleNames(object):
        MEMBER_PREFIX = "Is_Member_Of_"
        ACTION_PREFIX = "Can_"

        @staticmethod
        def get_membership(membership=""):
            return "{prefix}{membership}".format(prefix=RoleNames.MEMBER_PREFIX, membership=membership)

        @staticmethod
        def get_role_action(action_role):
            return "{prefix}{action_role}".format(prefix=RoleNames.ACTION_PREFIX, action_role=action_role)

    """
    action_roles - Array What action roles are required, implies and, (e.g. edit/run/delete/create).
                    Only if the current user has a limited
                   permission, such as Can_edit_BA do we need to check datastore owner.
    """

    # json response for failed authorization (error code 403)
    def response_authorization_error(error, code=403):
        return make_response(error, code)

    # Retrieve all its Is_Member_Of roles.
    def get_datastore_owner_membership_roles(user, kwargs):

        # Not authorizing post for DATASTORE (create datastore)
        # We place all calls after @fetch_model to already get he object (Action, WF, WF_instance, ds)
        datastore_data = None
        if kwargs.get("datastore") and kwargs.get("datastore").data:
            datastore_data = kwargs.get("datastore").data

        elif kwargs["workflow"] and kwargs["workflow"].data and kwargs["workflow"].data.datastore_id:
            tmp_ds = get_known_entity("datastore", kwargs["workflow"].data.datastore_id)
            if tmp_ds and tmp_ds.data:
                datastore_data = tmp_ds.data

        elif kwargs["workflow_instance"] and kwargs["workflow_instance"].data and kwargs["workflow_instance"].data.datastore_id:
                tmp_ds = get_known_entity("datastore", kwargs["workflow_instance"].data.datastore_id)
                if tmp_ds and tmp_ds.data:
                    datastore_data = tmp_ds.data

        elif kwargs["action"] and kwargs["action"].data and kwargs["action"].data.datastore_id:
                tmp_ds = get_known_entity("datastore", kwargs["action"].data.datastore_id)
                if tmp_ds and tmp_ds.data:
                    datastore_data = tmp_ds.data

        actions, memberships, is_member_all = get_current_user_permssions(datastore_data.user_id if hasattr(datastore_data, "user_id") else None)
        if is_member_all and user != DART_CLIENT_NAME:
            # datastore_data.user_id = current_user.email
            # TODO: Should we overwrite the user by whoever runs it?
            pass

        return memberships, is_member_all

    def get_current_user_permssions(user):
        if (user == None or user == "" or user == "anonymous" or user == "unknown"):
            _logger.debug("Assuming user {user} is member of all memberships groups".format(user=user))
            return [], [], True

        user_roles_service = current_app.dart_context.get(UserRolesService)
        actions, memberships = user_roles_service.get_user_roles(user)
        return actions, memberships, False # the Can_ prefixed roles and is_Member_Of prefix roles

    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):

            user = 'anonymous'
            if current_user and current_user.email:
                user = current_user.email
                _logger.debug("Authorizing user={user}, action_roles={action_roles}".format(
                    user=user, action_roles=action_roles))
            else:
                _logger.error("Cannot authorize anonymous user. user={user}, action_roles={action_roles}".format(
                    user=user, action_roles=action_roles))
                return response_authorization_error("anonymous users are not allowed")

            # Verify input is in correct format for action_roles
            for action_role in action_roles:
                if action_role not in ActionRoles.all():
                    _logger.error("Missing action_roles, not in ActionRoles {all}. user={user}, action_roles={action_roles}".format(
                        user=user, action_roles=action_roles, all=ActionRoles.all()))
                    return response_authorization_error("action-roles only allow %s values" % ActionRoles.all())

            # internal dart user, has superuser privileges
            if user != DART_CLIENT_NAME:
                # get current user's permission from the permission service.
                # We expect them to be prefixed by Is_Member_Of (members) or Can_ (actions).
                # Ideally we cache these values.
                current_user_actions, current_user_memberships, _ignore = get_current_user_permssions(user)
                if RoleNames.get_membership('Admin') not in current_user_memberships:
                    ds_memberships, is_member_all = get_datastore_owner_membership_roles(user, kwargs)

                    # intersection of current user memberships and datastore memberships
                    # For simplicity we might want to make sure ds owner belongs to a single group (e.g special PS user)
                    # We should not place this decorator on create datastore endpoint (it will always fail).
                    # In case of datastore having "", anonymous or unknown we let the user execute the operation
                    # (thus shared_memberships = current_user_memberships).
                    shared_memberships = list(set(current_user_memberships) & set(ds_memberships))
                    if is_member_all:
                        shared_memberships = list(set(current_user_memberships))

                    if not shared_memberships:
                        err = "Current user memberships {current_user_memberships} do not overlap with datastore's meberships {ds_memberships}". \
                            format(current_user_memberships=current_user_memberships, ds_memberships=ds_memberships)
                        _logger.error(err)
                        return response_authorization_error(err)

                    # If we do not have top level (E.g. Can_Run) roles we need to make sure we have membership level
                    # permission. E.g. Can_Run_BA, where the group (BA) is a group shared between current_user and ds owner groups.
                    missing_top_level_roles = [] # E.g. Can_Run is missing when action_role is RUN. Could exist Can_Run_BA.
                    for action_role in action_roles:
                        role = RoleNames.get_role_action(action_role)
                        if role not in current_user_actions:
                            missing_top_level_roles.append(role)

                    if missing_top_level_roles:
                        group_names = [membership.lstrip(RoleNames.get_membership("")) for membership in shared_memberships]# E.g. 'Is_Member_Of_BA' => 'BA'
                        group_roles= []
                        for missing_role in missing_top_level_roles:
                            group_roles.extend(["{mr}_{group}".format(mr=missing_role, group=group_name) for group_name in group_names])
                        if not (set(group_roles) & set(current_user_actions)):
                            _logger.error("group specific roles {group_roles} not exisiting for user's permissions {current_user_actions}. user={user}, action_roles={action_roles}".
                                          format(user=user, action_roles=action_roles, current_user_actions=current_user_actions, group_roles=group_roles))
                            return response_authorization_error("Missing group level role for action %s" % missing_role)

            # clear to run
            return f(*args, **kwargs)
        return wrapped_f
    return wrap



