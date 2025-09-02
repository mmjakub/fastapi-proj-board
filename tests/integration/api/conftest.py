import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.endpoints.dependencies import get_session_factory
from app.endpoints.dependencies import get_crypt_context
from app.main import app


@pytest.fixture()
async def client(session_factory):
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    return TestClient(app)


@pytest.fixture()
async def user_alice_exists(session, client):
    await session.execute(
        text(
            'INSERT INTO user (id, username, password) VALUES (1, "alice", :pw)'
        ).bindparams(pw=get_crypt_context().hash("alice"))
    )
