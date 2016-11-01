import logging
from dart.context.locator import injectable
from dart.context.database import db
from dart.model.orm import UserRolesDao


_logger = logging.getLogger(__name__)


@injectable
class UserRolesService(object):
    def __init__(self):
        pass

    @staticmethod
    def get_user_roles(user_id, raise_when_missing=True):
        """ :rtype: dart.model.user_roles.UserRoles """
        user_roles_dao = UserRolesDao.query.filter(UserRolesDao.user_id.like(user_id)).first()
        if not user_roles_dao and raise_when_missing:
            raise Exception('Roles for user with id=%s are not found' % user_id)
        return user_roles_dao.action_roles, user_roles_dao.membership_roles