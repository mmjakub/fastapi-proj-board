from fastapi.testclient import TestClient


def test_can_create_project_and_then_view_details_and_list(client: TestClient):
    project_info = {"name": "test", "description": "testing"}
    res = client.post("/projects", json=project_info)

    assert res.status_code == 201
    json = res.json()
    assert "id" in json
    assert json["documents"] == []
    assert json["owner"] == "test_user"
    assert json["info"] == project_info

    project_id = json["id"]
    res = client.get("/projects")
    assert res.status_code == 200
    json = res.json()
    assert len(json) == 1
    assert json[0]["id"] == project_id

    res = client.get(f"/projects/{project_id}/info")

    assert res.status_code == 200
    assert res.json() == project_info
