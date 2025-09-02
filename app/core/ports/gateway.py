from typing import Any, Callable, ParamSpec, Protocol


class PasswordHashGateway(Protocol):
    def hash(self, plain: str) -> str: ...

    def verify(self, plain: str, hash: str) -> bool:
        return hash == self.hash(plain)


P = ParamSpec("P")


class TaskQueueGateway(Protocol):
    def add_task(self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> int | None: ...
