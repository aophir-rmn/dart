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
_logger = logging.getLogger(__name__)

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

def does_key_exist(kwargs, dart_type):
    return kwargs.get(dart_type) and \
           hasattr(kwargs.get(dart_type), 'data') and \
           hasattr(kwargs[dart_type].data, 'datastore_id')

# Retrieve all its Is_Member_Of roles.
def get_datastore_owner_membership_roles(user, user_roles_service, get_known_entity, kwargs):
    _logger.info("Authorization: kwargs={0}".format(kwargs))

    # Not authorizing post for DATASTORE (create datastore)
    # We place all calls after @fetch_model to already get he object (Action, WF, WF_instance, ds)
    datastore_data = None
    if kwargs.get("datastore") and hasattr(kwargs.get("datastore"), 'data'):
        datastore_data = kwargs.get("datastore").data

    elif does_key_exist(kwargs=kwargs, dart_type="workflow"):
        tmp_ds = get_known_entity("datastore", kwargs["workflow"].data.datastore_id)
        if tmp_ds and tmp_ds.data:
            datastore_data = tmp_ds.data

    elif does_key_exist(kwargs=kwargs, dart_type="workflow_instance"):
        tmp_ds = get_known_entity("datastore", kwargs["workflow_instance"].data.datastore_id)
        if tmp_ds and tmp_ds.data:
            datastore_data = tmp_ds.data

    elif does_key_exist(kwargs=kwargs, dart_type="action"):
        tmp_ds = get_known_entity("datastore", kwargs["action"].data.datastore_id)
        if tmp_ds and tmp_ds.data:
            datastore_data = tmp_ds.data

    datastore_user_id = datastore_data.user_id if hasattr(datastore_data, "user_id") else None
    actions, memberships, is_member_all = get_current_user_permssions(datastore_user_id, user_roles_service)

    return datastore_user_id, memberships, is_member_all

# returns a triplet of action_roles, membership roles,is_member_all_groups (['Can_edit], ['is_Member_Of_BA'], False)
# is_member_all_groups is for legacy datastores that were created with anonymous/unknown or none
def get_current_user_permssions(user, user_roles_service):
    if user == None or user == "" or user == "anonymous" or user == "unknown":
        _logger.info("Authorization: Assuming user {user} is member of all memberships groups".format(user=user))
        return [], [], True

    actions = []
    memberships = []
    try:
        actions, memberships = user_roles_service.get_user_roles(user)
    except Exception as err:
        error_str = "Authorization: Cannot retrieve user from user_roles table. error: {error}".format(error=err)
        _logger.error(error_str)

    return actions, memberships, False # the Can_ prefixed roles and is_Member_Of prefix roles

# user_ - the current user (email) we try to authorize
# DEBUG_ID_ - unique uuid for this invocation used to track logs belonging to the same call to this function.
# dart_client_name_ - the superuser name as provided in the config file 'authorization.dart_client_name'
# current_user_actions_ - Can_XXX roles assigned to current user
# current_user_memberships - Is_Member_Of_XXX roles assigned to current user
# datastore_user_id_ - the user_id associated with the datastore of the action/workflow/datastore whose api endpoint
#                      we called. e.g POST /api/1/workflow
# ds_memberships_ - Is_Member_Of_XXX roles assigned to associated datastore's user
# is_ds_member_all_ - edge case where we only use the curent user's memberships when user is None/""/anonymous/unknown
# action_roles_ - The roles specified in the api endpoint that was called. E.g. @required_roles(['Edit'])
#                 This is the role we try to authorize against
def authorization_decorator(user_, DEBUG_ID_, dart_client_name_, current_user_actions_ ,current_user_memberships_,
                            datastore_user_id_, ds_memberships_, is_ds_member_all_, action_roles_):
    if user_ == dart_client_name_:
        _logger.info("{debug} Authorization: User {user} is the dart client superuser".format(user=user_, debug=DEBUG_ID_))

    # We skip checking permissions if the user is admin/superuser
    if user_ != dart_client_name_ and RoleNames.get_membership('Admin') not in current_user_memberships_:

        # intersection of current user memberships and datastore memberships
        # For simplicity we might want to make sure ds owner belongs to a single group (e.g special PS user)
        # We should not place this decorator on create datastore endpoint (it will always fail).
        # In case of datastore having "", anonymous or unknown we let the user execute the operation
        # (thus shared_memberships = current_user_memberships).
        shared_memberships = list(set(current_user_memberships_) & set(ds_memberships_))
        if is_ds_member_all_:
            shared_memberships = list(set(current_user_memberships_))

        if not shared_memberships:
            return """{debug} Current user's {user} memberships {current_user_memberships} do not
overlap with datastore's user owner {ds_user} meberships {ds_memberships}""". \
                     format(current_user_memberships=current_user_memberships_, ds_memberships=ds_memberships_,
                            user=user_, ds_user=datastore_user_id_, debug=DEBUG_ID_)
        else:
            _logger.info(DEBUG_ID_ + "shared_memberships={shared}".format(shared=shared_memberships))

        # If we do not have top level (E.g. Can_Run) roles we need to make sure we have membership level
        # permission. E.g. Can_Run_BA, where the group (BA) is a group shared between current_user and ds owner groups.
        missing_top_level_roles = [] # E.g. Can_Run is missing when action_role is RUN. Could exist Can_Run_BA.
        for action_role in action_roles_:
            role = RoleNames.get_role_action(action_role)
            if role not in current_user_actions_:
                missing_top_level_roles.append(role)

        _logger.info(DEBUG_ID_ + "missing_top_level_roles={missing}".format(missing=missing_top_level_roles))
        if missing_top_level_roles:
            group_names = [membership.lstrip(RoleNames.get_membership("")) for membership in shared_memberships]# E.g. 'Is_Member_Of_BA' => 'BA'
            group_roles = []
            for missing_role in missing_top_level_roles:
                group_roles.extend(["{mr}_{group}".format(mr=missing_role, group=group_name) for group_name in group_names])

            _logger.info(DEBUG_ID_ + "group_roles={group_roles}".format(group_roles=group_roles))
            if not (set(group_roles) & set(current_user_actions_)):
                return """{debug} group specific roles {group_roles} not exisiting for user's permissions
{current_user_actions}. user={user}, action_roles={action_roles}""". \
                         format(debug=DEBUG_ID_, user=user_, action_roles=action_roles_,
                                current_user_actions=current_user_actions_, group_roles=group_roles)

    return None

# user - the current user (email) we try to authorize
# kwargs - paramaters sent via the decorator (def wrapped_f(*args, **kwargs))
# user_roles_service - Service function to access the DAO holding user roles.
# get_known_entity - a function that return the model of an object by its name and id. Used by
#                     get_datastore_owner_membership_roles, e.g. get_known_entity("datastore", datastore_id)
# debug_uuid - unique uuid for this invocation used to track logs belonging to the same call to this function.
# action_roles - The roles specified in the api endpoint that was called. E.g. @required_roles(['Edit'])
#                This is the role we try to authorize against.
# dart_client_name - the superuser name as provided in the config file 'authorization.dart_client_name'
def prepare_inputs(current_user, kwargs, user_roles_service, get_known_entity, debug_uuid, action_roles, dart_client_name):
    inputs = {k: None for k in ['user_', 'DEBUG_ID_', 'dart_client_name_', 'current_user_actions_',
                                'current_user_memberships_', 'datastore_user_id_', 'ds_memberships_',
                                'is_ds_member_all_']}

    user = 'anonymous'
    if current_user and hasattr(current_user, 'email'):
        user = current_user.email
        inputs['user_'] = user
        _logger.info("Authorization: Authorizing user={user}, action_roles={action_roles}".format(
            user=current_user, action_roles=action_roles))
    else:
        return "Authorization: Cannot authorize user without email. user={user}, action_roles={action_roles}".format(
                 user=current_user, action_roles=action_roles)

    DEBUG_ID = "Authorization: {user}-{id} ".format(user=user, id=debug_uuid)
    inputs['DEBUG_ID_'] = DEBUG_ID

    # Verify input is in correct format for action_roles
    for action_role in action_roles:
        if action_role not in ActionRoles.all():
            return "{debug} Missing action_roles, not in ActionRoles {all}. user={user}, action_roles={action_roles}".format(
                     user=user, action_roles=action_roles, all=ActionRoles.all(), debug=DEBUG_ID)

    # Get current user permission if the user is not the superuser.
    # We expect them to be prefixed by Is_Member_Of (members) or Can_ (actions).
    inputs['current_user_actions_'] = []
    inputs['current_user_memberships_'] = []
    inputs['ds_memberships_'] = []
    if user != dart_client_name:
        current_user_actions, current_user_memberships, _ignore = get_current_user_permssions(user, user_roles_service)
        inputs['current_user_actions_'] = current_user_actions
        inputs['current_user_memberships_'] = current_user_memberships
        _logger.info(DEBUG_ID + "current_user_actions={actions}, current_user_memberships={memberships}". \
                     format(memberships=current_user_memberships, actions=current_user_actions))

        if (not current_user_actions) and (not current_user_memberships) and (not _ignore):
            err = "{debug} Current user's {user} is likely not in database.".format(user=user, debug=DEBUG_ID)
            return err

        # If the user is an admin we do not need to retrieve the datastore owner, yes otherwise
        if RoleNames.get_membership('Admin') in current_user_memberships:
            _logger.info("{debug} User {user} is an admin".format(user=user, debug=DEBUG_ID))

        if RoleNames.get_membership('Admin') not in current_user_memberships:
            datastore_user_id, ds_memberships, is_member_all = \
                get_datastore_owner_membership_roles(user=user,
                                                     user_roles_service=user_roles_service,
                                                     get_known_entity=get_known_entity,
                                                     kwargs=kwargs)
            inputs['datastore_user_id_'] = datastore_user_id
            inputs['ds_memberships_'] = ds_memberships
            inputs['is_ds_member_all_'] = is_member_all
            _logger.info(DEBUG_ID + "datastore_user_id={ds_user}, ds_membership={ds_mem}, member of all= {is_all}". \
                     format(ds_user=datastore_user_id, ds_mem=ds_memberships, is_all=is_member_all))

    return inputs



