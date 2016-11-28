from dart.model.base import BaseModel, dictable

@dictable
class AuthorizationRoles(BaseModel):
    def __init__(self, role_id, role_name):
        """
        :type role_id: str
        :type role_name: str
        """
        self.role_id = role_id
        self.role_name = role_name
