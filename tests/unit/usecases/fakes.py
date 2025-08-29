import itertools

from app.core.models import User, Username
from app.core.ports.repository import UserRepository
from app.core.ports.gateway import PasswordHashGateway


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[tuple[Username, str]] = []):
        self.id_gen = itertools.count(1)
        self.users = {u: User(next(self.id_gen), u, pw) for u, pw in users}

    async def get_or_none(self, username: Username) -> User | None:
        print(self.users)
        return self.users.get(username)

    async def exists(self, username: Username) -> bool:
        return username in self.users

    async def create(self, username: Username, password) -> User:
        user = User(next(self.id_gen), username, password)
        self.users[username] = user
        return user


class FakePasswordHashGateway(PasswordHashGateway):
    def hash(self, plain: str) -> str:
        return plain
