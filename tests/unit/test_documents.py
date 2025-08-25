from io import BytesIO
from uuid import uuid4

import pytest

from app.errors import ProjectNotFound, DocumentNotFound, ForbiddenError
import app.transaction_script as ts


@pytest.fixture()
def file() -> BytesIO:
    return BytesIO(b"test content")


@pytest.fixture()
def filename() -> str:
    return "test_file.txt"


@pytest.fixture()
def new_file() -> BytesIO:
    return BytesIO(b"new content")


@pytest.fixture()
def new_filename() -> str:
    return "new_file.txt"


@pytest.fixture()
async def setup_document_id(file, filename, Session, file_service):
    return (await ts.upload_document_to_proj(1, "alice", Session, file, filename, file_service))["id"]


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_owner_can_list_documents(Session):
    documents = await ts.get_proj_documents(1, "alice", Session)
    assert documents == []


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_list_documents(Session):
    documents = await ts.get_proj_documents(1, "bob", Session)
    assert documents == []


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_list_documents(Session):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.get_proj_documents(1, "bob", Session)
    assert exc_info.value.reason == "Must be project collaborator to do this"


async def test_cannot_list_documents_of_nonexisting_project(Session, file_service):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.delete_project(1, "alice", Session, file_service)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_owner_can_upload_documents(Session, file_service, file, filename):
    document = await ts.upload_document_to_proj(1, "alice", Session, file, filename, file_service)
    assert document["filename"] == filename
    assert document["id"]

    documents = await ts.get_proj_documents(1, "alice", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "alice", Session, file_service)
    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()

    documents = await ts.get_proj_documents(1, "bob", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "bob", Session, file_service)
    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_upload_documents(Session, file_service, file, filename):
    document = await ts.upload_document_to_proj(1, "bob", Session, file, filename, file_service)

    documents = await ts.get_proj_documents(1, "alice", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "alice", Session, file_service)
    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()

    documents = await ts.get_proj_documents(1, "bob", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "bob", Session, file_service)
    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_upload_documents(Session, file_service, file, filename):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.upload_document_to_proj(1, "bob", Session, file, filename, file_service)
    assert exc_info.value.reason == "Must be project collaborator to do this"


async def test_cannot_upload_documents_to_nonexisting_project(Session, file_service, file, filename):
    with pytest.raises(ProjectNotFound) as exc_info:
        await ts.upload_document_to_proj(1, "bob", Session, file, filename, file_service)
    assert exc_info.value.reason == "<Project:1> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_owner_can_update_documents(Session, file_service, setup_document_id, new_file, new_filename):
    document = await ts.update_document(setup_document_id, "alice", Session, new_file, new_filename, file_service)

    documents = await ts.get_proj_documents(1, "alice", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "alice", Session, file_service)
    assert dl_filename == new_filename
    new_file.seek(0)
    assert dl_file.read() == new_file.read()

    documents = await ts.get_proj_documents(1, "bob", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "bob", Session, file_service)
    assert dl_filename == new_filename
    new_file.seek(0)
    assert dl_file.read() == new_file.read()


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_update_documents(Session, file_service, setup_document_id, new_file, new_filename):
    document = await ts.update_document(setup_document_id, "alice", Session, new_file, new_filename, file_service)

    documents = await ts.get_proj_documents(1, "alice", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "alice", Session, file_service)
    assert dl_filename == new_filename
    new_file.seek(0)
    assert dl_file.read() == new_file.read()

    documents = await ts.get_proj_documents(1, "bob", Session)
    assert len(documents) == 1
    assert documents[0]["id"] == document["id"]
    assert documents[0]["filename"] == document["filename"]

    dl_file, dl_filename = await ts.download_document(document["id"], "bob", Session, file_service)
    assert dl_filename == new_filename
    new_file.seek(0)
    assert dl_file.read() == new_file.read()


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_update_documents(Session, file_service, setup_document_id, new_file, new_filename):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.update_document(setup_document_id, "charlie", Session, new_file, new_filename, file_service)
    assert exc_info.value.reason == "Must be project collaborator to do this"


async def test_cannot_update_nonexisting_document(Session, file_service, new_file, new_filename):
    document_id = uuid4()
    with pytest.raises(DocumentNotFound) as exc_info:
        await ts.update_document(document_id, "alice", Session, file, filename, file_service)
    assert exc_info.value.reason == f"<Document:{document_id}> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_owner_can_download_document(Session, file_service, file, filename, setup_document_id):
    dl_file, dl_filename = await ts.download_document(setup_document_id, "alice", Session, file_service)

    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_download_document(Session, file_service, file, filename, setup_document_id):
    dl_file, dl_filename = await ts.download_document(setup_document_id, "bob", Session, file_service)

    assert dl_filename == filename
    file.seek(0)
    assert dl_file.read() == file.read()


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_download_document(Session, file_service, setup_document_id, new_file, new_filename):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.download_document(setup_document_id, "charlie", Session, file_service)
    assert exc_info.value.reason == "Must be project collaborator to do this"


async def test_cannot_download_nonexisting_document(Session, file_service, new_file, new_filename):
    document_id = uuid4()
    with pytest.raises(DocumentNotFound) as exc_info:
        await ts.download_document(document_id, "alice", Session, file_service)
    assert exc_info.value.reason == f"<Document:{document_id}> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_owner_can_delete_document(Session, file_service, file, filename, setup_document_id):
    await ts.delete_document(setup_document_id, "alice", Session, file_service)

    documents = await ts.get_proj_documents(1, "alice", Session)
    assert len(documents) == 0

    with pytest.raises(DocumentNotFound) as exc_info:
        await ts.download_document(setup_document_id, "alice", Session, file_service)
    assert exc_info.value.reason == f"<Document:{setup_document_id}> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice", "invite_bob_to_test_project")
async def test_collaborator_can_delete_document(Session, file_service, file, filename, setup_document_id):
    await ts.delete_document(setup_document_id, "bob", Session, file_service)

    documents = await ts.get_proj_documents(1, "bob", Session)
    assert len(documents) == 0

    with pytest.raises(DocumentNotFound) as exc_info:
        await ts.download_document(setup_document_id, "alice", Session, file_service)
    assert exc_info.value.reason == f"<Document:{setup_document_id}> does not exist"


@pytest.mark.usefixtures("create_test_project_for_alice")
async def test_others_cannot_delete_document(Session, file_service, setup_document_id, new_file, new_filename):
    with pytest.raises(ForbiddenError) as exc_info:
        await ts.delete_document(setup_document_id, "charlie", Session, file_service)
    assert exc_info.value.reason == "Must be project collaborator to do this"


async def test_cannot_delete_nonexisting_document(Session, file_service, new_file, new_filename):
    document_id = uuid4()
    with pytest.raises(DocumentNotFound) as exc_info:
        await ts.delete_document(document_id, "alice", Session, file_service)
    assert exc_info.value.reason == f"<Document:{document_id}> does not exist"
