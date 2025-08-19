from .endpoints.schema import OAuthErrorValue


class UnauthorizedError(Exception):
    pass


class OAuthException(Exception):
    def __init__(self, error: OAuthErrorValue, error_description: str | None = None, status_code: int = 400):
        self.error = error
        self.error_description = error_description
        self.status_code = status_code


class InvalidGrantException(OAuthException):
    def __init__(self):
        super().__init__(error="invalid_grant", error_description="Invalid username/password")
