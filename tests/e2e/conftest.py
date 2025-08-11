from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.file_service import FileService, FakeFileService
from app.main import app
from app.models import Base, User
from app.dependencies import get_db_session, get_file_service
from app.jwt import get_username_from_jwt

TEST_USERNAME = "test_user"


async def create_user(session: AsyncSession, username: str) -> None:
    async with session.begin():
        session.add(User(username=username, password=username))


async def inmemory_session() -> async_sessionmaker:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine)
    async with Session() as session:
        await create_user(session, TEST_USERNAME)
    return Session


def fake_file_service() -> FileService:
    return FakeFileService()


@pytest.fixture()
def client() -> TestClient:
    app.dependency_overrides[get_db_session] = inmemory_session
    app.dependency_overrides[get_file_service] = fake_file_service
    app.dependency_overrides[get_username_from_jwt] = lambda: TEST_USERNAME
    return TestClient(app)
