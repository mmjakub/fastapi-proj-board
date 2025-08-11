import asyncio

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.file_service import FakeFileService
from app.main import app
from app.models import Base, User
from app.dependencies import get_db_session, get_file_service
from app.jwt import get_username_from_jwt
from app.routers.auth import pwd_context

TEST_USERS = "alice", "bob"


async def create_user(session: AsyncSession, username: str) -> None:
    async with session.begin():
        session.add(User(username=username, password=pwd_context.hash(username)))


async def create_inmemory_session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine)

    async with Session() as session:
        for username in TEST_USERS:
            await create_user(session, username)

    return Session


@pytest.fixture()
def client() -> TestClient:
    Session = asyncio.run(create_inmemory_session())
    file_service = FakeFileService()
    app.dependency_overrides[get_db_session] = lambda: Session
    app.dependency_overrides[get_file_service] = lambda: file_service
    app.dependency_overrides[get_username_from_jwt] = lambda: TEST_USERS[0]
    return TestClient(app)


@pytest.fixture()
def Session(client: TestClient) -> async_sessionmaker[AsyncSession]:
    return client.app.dependency_overrides[get_db_session]()  # type: ignore
