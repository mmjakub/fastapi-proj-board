from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.adapters.sql_alchemy import orm


async def test_can_load_users(session):
    await session.execute(
        text(
            "INSERT INTO user (id, username, password) VALUES"
            '(1, "alice", "alice123"),'
            '(2, "bob", "bob!@#")'
        )
    )
    expected = [
        orm.User(id=1, username="alice", password="alice123"),
        orm.User(id=2, username="bob", password="bob!@#"),
    ]

    result = await session.scalars(select(orm.User))

    assert result.all() == expected


async def test_can_save_users(session):
    users = [
        orm.User(id=1, username="alice", password="alice123"),
        orm.User(id=2, username="bob", password="bob!@#"),
    ]

    for user in users:
        session.add(user)
    await session.flush()

    rows = list(await session.execute(text("SELECT id, username, password from user")))
    assert rows == [(1, "alice", "alice123"), (2, "bob", "bob!@#")]


async def test_can_load_projects(session):
    await session.execute(
        text(
            "INSERT INTO project (id, owner_id, name, description) VALUES"
            "(1, 1, 'test1', 'testing1'),"
            "(2, 2, 'test2', 'testing2')"
        )
    )

    expected = [
        orm.Project(id=1, owner_id=1, name="test1", description="testing1"),
        orm.Project(id=2, owner_id=2, name="test2", description="testing2"),
    ]

    results = await session.scalars(select(orm.Project))
    assert results.all() == expected


async def test_can_save_projects(session):
    projects = [
        orm.Project(id=1, owner_id=1, name="test1", description="testing1"),
        orm.Project(id=2, owner_id=2, name="test2", description="testing2"),
    ]
    for project in projects:
        session.add(project)
    await session.flush()

    rows = list(
        await session.execute(
            text("SELECT id, owner_id, name, description FROM project")
        )
    )
    assert rows == [(1, 1, "test1", "testing1"), (2, 2, "test2", "testing2")]


async def test_can_retrieve_project_owner(session):
    await session.execute(
        text(
            'INSERT INTO user (id, username, password) VALUES (1, "alice", "alice123")'
        )
    )
    await session.execute(
        text(
            "INSERT INTO project (id, owner_id, name, description) VALUES "
            '(1, 1, "test", "testing")'
        )
    )

    project = await session.scalar(
        select(orm.Project).options(selectinload(orm.Project.owner))
    )

    assert project.owner == orm.User(id=1, username="alice", password="alice123")
