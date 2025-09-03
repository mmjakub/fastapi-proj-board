import pytest

from tests.integration.api.utils import auth_user


@pytest.mark.usefixtures(
    "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
def test_logged_in_user_can_list_projects(client):
    with auth_user(client, "alice"):
        response = client.get("/projects")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [
        {
            "documents": [{"filename": "foo", "id": 1}],
            "id": 1,
            "info": {"description": "testing", "name": "test"},
            "owner": "alice",
        }
    ]
    assert body["page"] == {
        "page_index": 0,
        "page_size": 1,
        "total_elements": 1,
        "total_pages": 1,
    }


def test_cannot_list_projects_without_logging_in(client):
    response = client.get("/projects")

    assert response.status_code == 401


@pytest.mark.usefixtures("user_alice_exists")
def test_user_can_create_a_project(client):
    with auth_user(client, "alice"):
        response = client.post(
            "/projects", json={"name": "new_project", "description": "foobar"}
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "info": {
            "name": "new_project",
            "description": "foobar",
        },
        "owner": "alice",
        "documents": [],
    }
    with auth_user(client, "alice"):
        response = client.get("/projects")

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "info": {
                "name": "new_project",
                "description": "foobar",
            },
            "owner": "alice",
            "documents": [],
        }
    ]


@pytest.mark.usefixtures(
    "alice_owns_a_project", "there_is_a_document_in_alices_project"
)
async def test_owner_can_delete_project(client, file_repository):
    with auth_user(client, "alice"):
        response = client.delete("/projects/1")

    assert response.status_code == 204
    with pytest.raises(FileNotFoundError):
        await file_repository.get(1)


@pytest.mark.usefixtures("alice_owns_a_project", "bob_works_on_alices_project")
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_view_project_info(client, user):
    with auth_user(client, user):
        response = client.get("/projects/1/info")

    assert response.status_code == 200
    assert response.json() == {"name": "test", "description": "testing"}


@pytest.mark.usefixtures("user_bob_exists")
def test_user_cannot_view_nonexistent_project_info(client):
    with auth_user(client, "bob"):
        response = client.get("/projects/1/info")

    assert response.status_code == 404


@pytest.mark.usefixtures("alice_owns_a_project", "user_bob_exists")
def test_external_user_cannot_view_project_info(client):
    with auth_user(client, "bob"):
        response = client.get("/projects/1/info")

    assert response.status_code == 403


@pytest.mark.usefixtures("alice_owns_a_project", "bob_works_on_alices_project")
@pytest.mark.parametrize("user", ["alice", "bob"])
def test_user_can_modify_project_info(client, user):
    new_info = {"name": "new_name", "description": "new_description"}
    with auth_user(client, user):
        response = client.put("/projects/1/info", json=new_info)

    assert response.status_code == 200
    assert response.json() == new_info


@pytest.mark.usefixtures("alice_owns_a_project", "user_bob_exists")
def test_external_user_cannot_modify_project_info(client):
    new_info = {"name": "new_name", "description": "new_description"}
    with auth_user(client, "bob"):
        response = client.put("/projects/1/info", json=new_info)

    assert response.status_code == 403


@pytest.mark.usefixtures("alice_owns_a_project", "user_bob_exists")
def test_project_owner_can_invite_another_user(client):
    with auth_user(client, "alice"):
        response = client.post("/projects/1/invite?user=bob")

    assert response.status_code == 200

    with auth_user(client, "bob"):
        response = client.get("/projects")
    assert response.json()["items"] == [
        {
            "documents": [],
            "id": 1,
            "info": {"description": "testing", "name": "test"},
            "owner": "alice",
        }
    ]


@pytest.mark.usefixtures(
    "alice_owns_a_project", "bob_works_on_alices_project", "user_charlie_exists"
)
def test_project_collaborator_cannot_invite_another_user(client):
    with auth_user(client, "bob"):
        response = client.post("/projects/1/invite?user=charlie")

    assert response.status_code == 403


@pytest.mark.usefixtures("alice_owns_a_project", "bob_works_on_alices_project")
def test_project_collaborator_cannot_be_invited_again(client):
    with auth_user(client, "alice"):
        response = client.post("/projects/1/invite?user=bob")

    assert response.status_code == 409
