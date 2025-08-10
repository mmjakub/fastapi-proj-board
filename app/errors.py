class UnauthorizedError(Exception):
    pass


class UsernameTaken(Exception):
    pass


class OAuthException(Exception):
    def __init__(
        self, error: str, error_description: str | None = None, status_code: int = 400
    ):
        self.error = error
        self.error_description = error_description
        self.status_code = status_code

    def content(self):
        res = {"error": self.error}
        if self.error_description:
            res["error_description"] = self.error_description
        return res


class InvalidGrantException(OAuthException):
    def __init__(self):
        super().__init__(
            error="invalid_grant", error_description="Invalid username/password"
        )
