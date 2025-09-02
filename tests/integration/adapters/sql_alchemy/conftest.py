import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)

from app.adapters.sql_alchemy import orm
from app.adapters.sql_alchemy.repository import SADataRepository


@pytest.fixture()
def engine() -> AsyncEngine:
    return create_async_engine("sqlite+aiosqlite:///:memory:")


@pytest.fixture()
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(orm.Base.metadata.create_all)
    return async_sessionmaker(engine)


@pytest.fixture()
async def session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture()
def project_repo(session):
    return SADataRepository(session)


@pytest.fixture()
async def user_alice_exists(session):
    await session.execute(
        text('INSERT INTO user (id, username, password) VALUES (1, "alice", "alice")')
    )


@pytest.fixture()
async def bob_works_on_alices_project(session):
    await session.execute(
        text('INSERT INTO user (id, username, password) VALUES (2, "bob", "bob")')
    )
    await session.execute(
        text("INSERT INTO collaborator (user_id, project_id) VALUES (2, 1);")
    )


@pytest.fixture()
async def alice_owns_a_project(session):
    await session.execute(
        text(
            "INSERT INTO project (id, owner_id, name, description) VALUES "
            '(1, 1, "test", "testing")'
        )
    )
    await session.execute(
        text("INSERT INTO collaborator (user_id, project_id) VALUES (1, 1);")
    )


@pytest.fixture()
async def there_is_a_document_in_alices_project(session):
    await session.execute(
        text(
            "INSERT INTO document (id, project_id, upload_filename) VALUES "
            '(1, 1, "foo")'
        )
    )
