from app.jwt import get_username_from_jwt


def test_login(client):
    del client.app.dependency_overrides[get_username_from_jwt]
    res = client.get("/projects")
    assert res.status_code == 401

    res = client.post("/login", data={"username": "alice", "password": "alice"})
    assert res.status_code == 200
    access_token = res.json()["access_token"]

    res = client.get("/projects", headers={"Authorization": f"Bearer {access_token}"})
    assert res.status_code == 200
