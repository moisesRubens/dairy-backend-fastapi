class ExpiredTokenException(Exception):
    def __init__(self, message="token already expired"):
        super().__init__(message)