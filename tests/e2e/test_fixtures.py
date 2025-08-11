from fastapi.testclient import TestClient


def test_fixtures(client: TestClient):
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "test_user"
