import os
import shutil
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.adapters.local_file.repository import LocalFileRepository
from app.endpoints.dependencies import get_session_factory, get_file_repository
from app.endpoints.dependencies import get_crypt_context
from app.jwt import create_access_token
from app.main import app


@pytest.fixture()
def file_repository():
    tmp_dir = os.urandom(8).hex()
    os.mkdir(tmp_dir)
    yield LocalFileRepository(tmp_dir)
    shutil.rmtree(tmp_dir)


@pytest.fixture()
async def client(session_factory, file_repository):
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_file_repository] = lambda: file_repository
    return TestClient(app)


@pytest.fixture()
async def user_alice_exists(session, client):
    await session.execute(
        text('INSERT INTO user (id, username, password) VALUES (1, "alice", :pw)').bindparams(
            pw=get_crypt_context().hash("alice")
        )
    )


@pytest.fixture()
async def there_is_a_document_in_alices_project(session, file_repository):
    await session.execute(text("INSERT INTO document (id, project_id, upload_filename) VALUES " '(1, 1, "foo")'))
    await file_repository.save(1, BytesIO(b"foobar"))


@pytest.fixture(scope="session")
def alice_jwt_token():
    token = create_access_token("alice")
    return token.access_token
