from dart.model.base import BaseModel, dictable

@dictable
class UserRoles(BaseModel):
    def __init__(self, user_id, action_roles, membership_roles):
        """
        :type role_id: str
        :type action_roles: jsonb
        :type membership_roles: jsonb
        """
        self.user_id = user_id
        self.action_roles = action_roles
        self.membership_roles = membership_roles
