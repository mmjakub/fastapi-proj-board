class ForbiddenError(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class ConflictError(Exception):
    pass


class CollaboratorConflict(ConflictError):
    pass


class UsernameConflict(ConflictError):
    pass
