import pytest
from sqlalchemy import text

from app.core.errors import ResourceNotFound
from app.core.models import Project, Document


@pytest.mark.usefixtures("user_alice_exists", "alice_owns_a_project")
async def test_can_load_a_simple_project(project_repo, session):
    expected = Project(
        id=1,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice"},
        documents=[],
    )

    project = await project_repo.get(1)

    assert project == expected


async def test_cannot_load_a_project_by_nonexistent_id(project_repo, session):

    with pytest.raises(ResourceNotFound):
        await project_repo.get(1)


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "bob_works_on_alices_project"
)
async def test_can_load_a_project_with_collaborators(project_repo, session):
    expected = Project(
        id=1,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice", "bob"},
        documents=[],
    )

    project = await project_repo.get(1)

    assert project == expected


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_can_load_a_project_with_documents(project_repo, session):
    await session.execute(
        text(
            "INSERT INTO document (id, project_id, upload_filename) VALUES "
            '(2, 1, "bar")'
        )
    )
    expected = Project(
        id=1,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice"},
        documents=[
            Document(id=1, project_id=1, upload_filename="foo"),
            Document(id=2, project_id=1, upload_filename="bar"),
        ],
    )

    project = await project_repo.get(1)

    assert project == expected


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_can_load_a_project_by_document_id(project_repo, session):
    expected = Project(
        id=1,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice"},
        documents=[
            Document(id=1, project_id=1, upload_filename="foo"),
        ],
    )

    project = await project_repo.get_by_document_id(1)

    assert project == expected


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_cannot_load_a_project_by_nonexistent_document_id(project_repo, session):
    with pytest.raises(ResourceNotFound):
        await project_repo.get_by_document_id(42)


@pytest.mark.usefixtures("user_alice_exists", "alice_owns_a_project")
async def test_can_load_all_projects_for_user(project_repo, session):
    await session.execute(text("INSERT INTO user VALUES " '(2, "bob", "bob")'))
    await session.execute(
        text('INSERT INTO project VALUES (2, 2, "test2", "testing2")')
    )
    await session.execute(text("INSERT INTO collaborator VALUES (1, 2), (2, 2)"))
    expected = [
        Project(
            id=1,
            name="test",
            description="testing",
            owner="alice",
            collaborators={"alice"},
            documents=[],
        ),
        Project(
            id=2,
            name="test2",
            description="testing2",
            owner="bob",
            collaborators={"alice", "bob"},
            documents=[],
        ),
    ]

    projects = await project_repo.get_all("alice")

    assert projects == expected


@pytest.mark.usefixtures("user_alice_exists")
async def test_can_save_new_project(project_repo, session):
    project = Project(
        id=None,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice"},
        documents=[],
    )

    actual = await project_repo.save(project)

    assert actual is not project
    project.id = 1
    assert actual == project
    [row] = await session.execute(
        text("SELECT id, owner_id, name, description FROM project")
    )
    assert row == (1, 1, "test", "testing")


@pytest.mark.usefixtures("user_alice_exists")
async def test_can_create_new_project(project_repo, session):
    expected = Project(
        id=1,
        name="test",
        description="testing",
        owner="alice",
        collaborators={"alice"},
        documents=[],
    )

    actual = await project_repo.create("alice", "test", "testing")

    assert actual == expected
    [row] = await session.execute(
        text("SELECT id, owner_id, name, description FROM project")
    )
    assert row == (1, 1, "test", "testing")


@pytest.mark.usefixtures("user_alice_exists", "alice_owns_a_project")
async def test_can_save_project_with_new_info(project_repo, session):
    project = Project(
        id=1,
        name="new_name",
        description="new_description",
        owner="alice",
        collaborators={"alice"},
        documents=[],
    )

    actual = await project_repo.save(project)

    assert actual == project
    [row] = await session.execute(
        text("SELECT id, owner_id, name, description FROM project")
    )
    assert row == (1, 1, "new_name", "new_description")


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_can_save_project_with_edited_document(project_repo, session):
    project = Project(
        id=1,
        name="new_name",
        description="new_description",
        owner="alice",
        collaborators={"alice"},
        documents=[Document(id=1, project_id=1, upload_filename="bar")],
    )

    actual = await project_repo.save(project)

    assert actual == project
    [row] = await session.execute(
        text("SELECT id, project_id, upload_filename FROM document")
    )
    assert row == (1, 1, "bar")


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_can_save_project_with_new_document(project_repo, session):
    project = Project(
        id=1,
        name="new_name",
        description="new_description",
        owner="alice",
        collaborators={"alice"},
        documents=[
            Document(id=1, project_id=1, upload_filename="foo"),
            Document(id=None, project_id=1, upload_filename="bar"),
        ],
    )

    actual = await project_repo.save(project)

    assert actual.documents[1].id == 2
    [existing_row, new_row] = await session.execute(
        text("SELECT id, project_id, upload_filename FROM document")
    )
    assert existing_row == (1, 1, "foo")
    assert new_row == (2, 1, "bar")


@pytest.mark.usefixtures(
    "user_alice_exists", "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_can_explicitly_create_new_document(project_repo, session):
    expected = Document(id=2, project_id=1, upload_filename="bar")
    actual = await project_repo.create_document(project_id=1, upload_filename="bar")

    assert actual == expected
    [existing_row, new_row] = await session.execute(
        text("SELECT id, project_id, upload_filename FROM document")
    )
    assert existing_row == (1, 1, "foo")
    assert new_row == (2, 1, "bar")
