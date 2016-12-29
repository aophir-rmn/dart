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
import uuid
from dart.config.config import configuration
from dart.service.user_roles import UserRolesService

from flask_login import current_user
from flask import make_response, current_app
from dart.web.api.entity_lookup import get_known_entity
from functools import wraps


from dart.auth.rmn_required_roles_impl  import prepare_inputs
from dart.auth.rmn_required_roles_impl  import authorization_decorator


_logger = logging.getLogger(__name__)
config_path = os.environ['DART_CONFIG']
config = configuration(config_path)
DART_CLIENT_NAME = config['authorization']['dart_client_name']


def dart_required_roles(action_roles):
  def wrap(f):
    @wraps(f)
    def wrapped_f(*args, **kwargs):

        try:
            inputs = prepare_inputs(current_user=current_user,
                                    kwargs=kwargs,
                                    user_roles_service=current_app.dart_context.get(UserRolesService),
                                    get_known_entity=get_known_entity,
                                    debug_uuid=uuid.uuid4().hex,
                                    action_roles=action_roles,
                                    dart_client_name=DART_CLIENT_NAME)
            if isinstance(inputs, basestring):
                _logger.error(inputs)
                return make_response(inputs, 403)

            # Else we assume inputs is a dictionary of params to authorization_decorator(...)
            inputs['dart_client_name_'] = DART_CLIENT_NAME
            inputs['action_roles_'] = action_roles
            err = authorization_decorator(**inputs)
            if err:
                _logger.error(err)
                return make_response(err, 403)

        # To catch unexpected errors and return 500 error.
        except Exception as err:
            return make_response(str(err), 500)

        # clear to run
        return f(*args, **kwargs)
    return wrapped_f
  return wrap

