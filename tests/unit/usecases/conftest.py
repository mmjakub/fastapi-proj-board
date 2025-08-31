from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from .fakes import FakeProjectRepository, FakeUserRepository, FakeTaskQueueGateway, FakeFileRepository
from app.core.models import Document, Project, Username
from app.core.ports.repository import FileRepository, ProjectRepository, UserRepository
from app.core.ports.gateway import TaskQueueGateway


@pytest.fixture()
def test_filename():
    return "foo.txt"


@pytest.fixture()
def new_filename():
    return "new.txt"


@pytest.fixture()
def test_file():
    return BytesIO(b"foo")


@pytest.fixture()
def new_file():
    return BytesIO(b"new")


@pytest.fixture()
def existing_document_id():
    return 1


@pytest.fixture()
def test_document_id():
    return 1


@pytest.fixture()
def created_document(test_filename, test_project_id, nonexistent_document_id):
    return Document(nonexistent_document_id, test_project_id, test_filename)


@pytest.fixture()
def test_document(test_filename, test_project_id, test_document_id):
    return Document(test_document_id, test_project_id, test_filename)


@pytest.fixture()
def nonexistent_document_id():
    return 42


@pytest.fixture()
def test_user() -> Username:
    return "test_user"


@pytest.fixture()
def collaborator() -> Username:
    return "collaborator"


@pytest.fixture()
def unrelated_user() -> Username:
    return "unrelated_user"


@pytest.fixture()
def test_project_id() -> int:
    return 1


@pytest.fixture()
def test_name() -> str:
    return "test"


@pytest.fixture()
def test_description() -> str:
    return "testing"


@pytest.fixture()
def test_documents() -> list[Document]:
    return [Document(1, 1, "foo.txt"), Document(2, 1, "bar.txt")]


@pytest.fixture()
def test_project(test_project_id, test_user, collaborator, test_name, test_description, test_documents):
    return Project(
        id=test_project_id,
        name=test_name,
        description=test_description,
        owner=test_user,
        collaborators={test_user, collaborator},
        documents=[*test_documents],
    )


@pytest.fixture()
def test_project2(test_project_id, test_user, collaborator, test_name, test_description):
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
    return FakeFileRepository([(1, "foo"), (2, "bar")])


@pytest.fixture()
def fake_tasks() -> TaskQueueGateway:
    return FakeTaskQueueGateway()


@pytest.fixture()
def mock_repo(test_project, created_document) -> ProjectRepository:
    mock = AsyncMock(ProjectRepository)
    mock.get.return_value = test_project
    mock.get_by_document_id.return_value = test_project
    mock.create_document.return_value = created_document
    return mock


@pytest.fixture()
def mock_user_repo() -> UserRepository:
    mock = AsyncMock(UserRepository)
    return mock


@pytest.fixture()
def mock_file_repo(test_project, test_file) -> FileRepository:
    mock = AsyncMock(FileRepository)
    mock.get.return_value = test_file
    return mock


@pytest.fixture()
def mock_tasks() -> TaskQueueGateway:
    return Mock(TaskQueueGateway)


@pytest.fixture()
def mock() -> MagicMock:
    return MagicMock()
