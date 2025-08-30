from unittest.mock import AsyncMock, Mock

import pytest

from .fakes import FakeProjectRepository, FakeUserRepository, FakeTaskQueueGateway, FakeFileRepository
from app.core.models import Document, Project, Username
from app.core.ports.repository import FileRepository, ProjectRepository, UserRepository
from app.core.ports.gateway import TaskQueueGateway


@pytest.fixture()
def test_user() -> Username:
    return "test_user_1"


@pytest.fixture()
def collaborator() -> Username:
    return "collaborator"


@pytest.fixture()
def unrelated_user() -> Username:
    return "unrelated_user"


@pytest.fixture()
def test_id() -> int:
    return 1


@pytest.fixture()
def test_name() -> str:
    return "test"


@pytest.fixture()
def test_description() -> str:
    return "testing"


@pytest.fixture()
def test_documents() -> tuple[Document, ...]:
    return Document(1, 1, "foo.txt"), Document(2, 1, "bar.txt")


@pytest.fixture()
def test_project(test_id, test_user, collaborator, test_name, test_description, test_documents):
    return Project(
        id=test_id,
        name=test_name,
        description=test_description,
        owner=test_user,
        collaborators={test_user, collaborator},
        documents=[*test_documents],
    )


@pytest.fixture()
def test_project2(test_id, test_user, collaborator, test_name, test_description):
    return Project(
        id=2,
        name=test_name + "2",
        description=test_description + "2",
        owner=test_user,
        collaborators={test_user, collaborator},
        documents=[],
    )


@pytest.fixture()
def new_project_info() -> tuple[str, str]:
    return "new_name", "new_description"


@pytest.fixture()
def updated_project(test_user, collaborator, new_project_info, test_documents):
    return Project(
        id=1,
        name=new_project_info[0],
        description=new_project_info[1],
        owner=test_user,
        collaborators={test_user, collaborator},
        documents=[*test_documents],
    )


@pytest.fixture()
def empty_fake_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture()
def fake_repo(test_project, test_project2) -> FakeProjectRepository:
    return FakeProjectRepository([test_project, test_project2])


@pytest.fixture()
def fake_user_repo(unrelated_user, collaborator) -> UserRepository:
    return FakeUserRepository([(unrelated_user, ""), (collaborator, "")])


@pytest.fixture()
def fake_file_repo() -> FileRepository:
    return FakeFileRepository([(1, "foo\n"), (2, "bar\n")])


@pytest.fixture()
def fake_tasks() -> TaskQueueGateway:
    return FakeTaskQueueGateway()


@pytest.fixture()
def mock_repo() -> ProjectRepository:
    return AsyncMock(ProjectRepository)


@pytest.fixture()
def mock_user_repo() -> UserRepository:
    return AsyncMock(UserRepository)


@pytest.fixture()
def mock_file_repo() -> FileRepository:
    return AsyncMock(FileRepository)


@pytest.fixture()
def mock_tasks() -> TaskQueueGateway:
    return Mock(TaskQueueGateway)
