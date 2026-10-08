class ExpiredTokenException(Exception):
    def __init__(self, message="token already expired"):
        super().__init__(message)

class InvalidCredentialsException(Exception):
    pass


class AdminPermissionRequired(Exception):
    pass


class PermissionDenied(Exception):
    pass
