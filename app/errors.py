class UnauthorizedError(Exception):
    pass


class OAuthException(Exception):
    def __init__(self, error: str, error_description: str | None = None, status_code: int = 400):
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
        super().__init__(error="invalid_grant", error_description="Invalid username/password")


class DomainError(Exception):
    reason: str = "Something went wrong"

    def __init__(self, *args, reason: str | None = None, **kwargs):
        if reason is not None:
            self.reason = reason
        super().__init__(self, *args, **kwargs)


class UsernameTaken(DomainError):
    reason: str = "Username is not available"


class ForbiddenError(DomainError):
    reason: str = "Action not allowed"


class ResourceNotFound(DomainError):

    def __init__(
        self,
        *args,
        resource_name: str = "Resource",
        resource=None,
        **kwargs,
    ):
        self.resource = resource
        self.resource_name = resource_name
        reason = f"<{self.resource_name}:{self.resource}> does not exist"
        super().__init__(*args, reason=reason, **kwargs)


class ProjectNotFound(ResourceNotFound):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, resource_name="Project", **kwargs)


class DocumentNotFound(ResourceNotFound):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, resource_name="Document", **kwargs)


class UserNotFound(ResourceNotFound):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, resource_name="User", **kwargs)
