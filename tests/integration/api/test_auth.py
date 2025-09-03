import pytest


def test_can_create_user_with_unique_username(client):
    response = client.post("/register", json={"username": "alice", "password": "alice"})

    assert response.status_code == 201
    assert response.json() == {
        "username": "alice",
        "owned_projects": [],
        "projects": [],
    }


@pytest.mark.usefixtures("user_alice_exists")
def test_cannot_create_user_with_duplicate_username(client):
    response = client.post("/register", json={"username": "alice", "password": "alice"})

    assert response.status_code == 409
    assert response.json() == {"error": "Username 'alice' is not available"}


@pytest.mark.usefixtures("user_alice_exists")
def test_can_login_with_valid_credentials(client):
    response = client.post("/login", data={"username": "alice", "password": "alice"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "Bearer"
    assert body["expires"] == 3600


@pytest.mark.usefixtures("user_alice_exists")
def test_cannot_login_with_invalid_password(client):
    response = client.post("/login", data={"username": "alice", "password": "wrong"})

    assert response.status_code == 400
    assert response.json() == dict(
        error="invalid_grant", error_description="Invalid username/password"
    )


@pytest.mark.usefixtures("user_alice_exists")
def test_cannot_login_with_invalid_username(client):
    response = client.post("/login", data={"username": "bob", "password": "bob"})

    assert response.status_code == 400
    assert response.json() == dict(
        error="invalid_grant", error_description="Invalid username/password"
    )
