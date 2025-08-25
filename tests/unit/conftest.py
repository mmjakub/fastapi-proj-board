import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.file_service import FakeFileService
from app.models import Base, User
import app.transaction_script as ts


TEST_USERS = "alice", "bob", "charlie", "diana"
TEST_PWD = tuple(ts.pwd_context.hash(u) for u in TEST_USERS)


@pytest_asyncio.fixture()
async def Session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine)

    async with Session() as session, session.begin():
        for username, password in zip(TEST_USERS, TEST_PWD):
            session.add(User(username=username, password=password))

    return Session


@pytest.fixture()
def file_service() -> FakeFileService:
    return FakeFileService()


@pytest_asyncio.fixture()
async def create_test_project_for_alice(Session) -> None:
    await ts.create_project("alice", "test_name", "test_description", Session)


@pytest_asyncio.fixture()
async def invite_bob_to_test_project(Session) -> None:
    await ts.invite_user("bob", 1, "alice", Session)
