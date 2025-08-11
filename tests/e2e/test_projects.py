import contextlib

from fastapi.testclient import TestClient

from app.jwt import get_username_from_jwt


@contextlib.contextmanager
def auth_user(username: str, client: TestClient):
    dep = client.app.dependency_overrides[get_username_from_jwt]  # type: ignore
    client.app.dependency_overrides[get_username_from_jwt] = lambda: username  # type: ignore
    yield
    client.app.dependency_overrides[get_username_from_jwt] = dep  # type: ignore


def test_can_create_project_and_then_view_details_and_list(client: TestClient):
    project_info = {"name": "test", "description": "testing"}
    res = client.post("/projects", json=project_info)

    assert res.status_code == 201
    json = res.json()
    assert json["id"] == 1
    assert json["documents"] == []
    assert json["owner"] == "alice"
    assert json["info"] == project_info

    res = client.get("/projects")
    assert res.status_code == 200
    json = res.json()
    assert len(json) == 1
    assert json[0]["id"] == 1

    res = client.get("/projects/1/info")

    assert res.status_code == 200
    assert res.json() == project_info


def test_can_invite_user_and_modify_info(client: TestClient):
    project_info = {"name": "test", "description": "testing"}
    new_project_info = {"name": "bob was here", "description": "bob is the best"}

    res = client.post("/projects", json=project_info)

    assert res.status_code == 201

    with auth_user("bob", client):
        res = client.get("/projects/1/info")
        assert res.status_code == 403
        res = client.put("/projects/1/info", json=new_project_info)
        assert res.status_code == 403

    res = client.post("/projects/1/invite", params={"user": "bob"})
    assert res.status_code == 200

    with auth_user("bob", client):
        res = client.put("/projects/1/info", json=new_project_info)
        assert res.status_code == 200
        assert res.json() == new_project_info
        res = client.get("/projects/1/info")
        assert res.status_code == 200
        assert res.json() == new_project_info

    res = client.get("/projects/1/info")
    assert res.status_code == 200
    assert res.json() == new_project_info
