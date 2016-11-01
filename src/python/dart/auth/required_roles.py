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

config_path = os.environ['DART_CONFIG']
config = configuration(config_path)
ENABLE_AUTHORIZATION = config['authorization']['enable']

if ENABLE_AUTHORIZATION:
    from rmn_required_roles import dart_required_roles
else:
    from no_authorization_required_roles import dart_required_roles

_logger = logging.getLogger(__name__)


def required_roles(action_roles):
    return dart_required_roles(action_roles)
