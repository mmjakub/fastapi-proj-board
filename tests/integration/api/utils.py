import contextlib

from fastapi.testclient import TestClient

from app.jwt import create_access_token


@contextlib.contextmanager
def auth_user(client: TestClient, username: str):
    token = create_access_token(username)
    _headers = client.headers.copy()
    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client
    client.headers = _headers
