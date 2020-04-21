from models import User


def check_user_is_not_admin(user: User):
    if user.isAdmin is True:
        raise UnauthorizedForAdminUser()


class ClientError(Exception):
    def __init__(self, field: str, error: str):
        self.errors = {}
        self.errors[field] = [error]

    def add_error(self, field, error):
        if field in self.errors:
            self.errors[field].append(error)
        else:
            self.errors[field] = [error]


class UnauthorizedForAdminUser(ClientError):
    def __init__(self):
        super().__init__('global',
                       "Le statut d'administrateur ne permet pas d'accéder au suivi des réservations")
