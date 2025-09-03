import pytest

from tests.integration.api.utils import auth_user


@pytest.mark.usefixtures(
    "there_is_a_document_in_alices_project", "bob_works_on_alices_project"
)
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_list_project_documents(client, user):
    with auth_user(client, user):
        response = client.get("/projects/1/documents")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [{"filename": "foo", "id": 1}]
    assert body["page"] == {
        "page_index": 0,
        "page_size": 1,
        "total_elements": 1,
        "total_pages": 1,
    }


@pytest.mark.usefixtures("alice_owns_a_project", "user_bob_exists")
def test_external_user_cannot_list_project_documents(client):
    with auth_user(client, "bob"):
        response = client.get("/projects/1/documents")
    assert response.status_code == 403


@pytest.mark.usefixtures("user_bob_exists")
def test_user_cannot_list_nonexistent_project_documents(client):
    with auth_user(client, "bob"):
        response = client.get("/projects/1/documents")
    assert response.status_code == 404


@pytest.mark.usefixtures(
    "there_is_a_document_in_alices_project", "bob_works_on_alices_project"
)
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_create_a_document(client, user):
    file = b"new_file_contents"
    filename = "new_file"
    with auth_user(client, user):
        response = client.post(
            "/projects/1/documents", files={"file": (filename, file)}
        )

    assert response.status_code == 201
    assert response.json() == {"filename": filename, "id": 2}


@pytest.mark.usefixtures("alice_owns_a_project", "user_bob_exists")
def test_external_user_cannot_create_a_document(client):
    with auth_user(client, "bob"):
        response = client.post("/projects/1/documents", files={"file": ("foo", b"bar")})
    assert response.status_code == 403


@pytest.mark.usefixtures(
    "there_is_a_document_in_alices_project", "bob_works_on_alices_project"
)
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_download_a_document(client, user):
    file = b"foobar"
    filename = "foo"
    with auth_user(client, user):
        response = client.get("/documents/1")

    assert response.status_code == 200
    assert response.read() == file
    assert f"filename={filename}" in response.headers["Content-Disposition"]


@pytest.mark.usefixtures("there_is_a_document_in_alices_project", "user_bob_exists")
def test_external_user_cannot_download_a_document(client):
    with auth_user(client, "bob"):
        response = client.get("/documents/1")
    assert response.status_code == 403


@pytest.mark.usefixtures("user_bob_exists")
def test_user_cannot_download_a_nonexistent_document(client):
    with auth_user(client, "bob"):
        response = client.get("/documents/1")
    assert response.status_code == 404


@pytest.mark.usefixtures(
    "there_is_a_document_in_alices_project", "bob_works_on_alices_project"
)
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_update_a_document(client, user):
    file = b"new_content"
    filename = "new_file"
    with auth_user(client, user):
        response = client.put("/documents/1", files={"file": (filename, file)})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "filename": filename}


@pytest.mark.usefixtures("there_is_a_document_in_alices_project", "user_bob_exists")
def test_external_user_cannot_update_a_document(client):
    with auth_user(client, "bob"):
        response = client.put("/documents/1", files={"file": ("a", b"a")})
    assert response.status_code == 403


@pytest.mark.usefixtures("user_bob_exists")
def test_user_cannot_update_a_nonexistent_document(client):
    with auth_user(client, "bob"):
        response = client.put("/documents/1", files={"file": ("a", b"a")})
    assert response.status_code == 404


@pytest.mark.usefixtures(
    "there_is_a_document_in_alices_project", "bob_works_on_alices_project"
)
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_delete_a_document(client, user):
    with auth_user(client, user):
        response = client.delete("/documents/1")

    assert response.status_code == 204


@pytest.mark.usefixtures("there_is_a_document_in_alices_project", "user_bob_exists")
def test_external_user_cannot_delete_a_document(client):
    with auth_user(client, "bob"):
        response = client.delete("/documents/1")
    assert response.status_code == 403


@pytest.mark.usefixtures("user_bob_exists")
def test_user_cannot_delete_a_nonexistent_document(client):
    with auth_user(client, "bob"):
        response = client.delete("/documents/1")
    assert response.status_code == 404
