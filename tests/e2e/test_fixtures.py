from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker


def test_client(client: TestClient):
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_Session(Session):
    assert type(Session) is async_sessionmaker
