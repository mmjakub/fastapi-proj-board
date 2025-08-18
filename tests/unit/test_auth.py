import pytest

import app.transaction_script as ts
from app.errors import InvalidGrantException, UsernameTaken


@pytest.mark.asyncio
async def test_login_good_credentials(Session):
    token = await ts.login("alice", "alice", Session)
    assert token.access_token


@pytest.mark.asyncio
async def test_login_bad_credentials(Session):
    with pytest.raises(InvalidGrantException):
        await ts.login("alice", "wrong_password", Session)


@pytest.mark.asyncio
async def test_user_info(Session):
    username, owned_projects, projects = await ts.me("alice", Session)
    assert username == "alice"
    assert owned_projects == projects == []


@pytest.mark.asyncio
async def test_can_register_if_username_is_available(Session):
    username = await ts.register("new_user", "pwd", Session)
    assert username == "new_user"


@pytest.mark.asyncio
async def test_cant_register_if_username_is_taken(Session):
    with pytest.raises(UsernameTaken) as exc_info:
        await ts.register("alice", "pwd", Session)
    assert exc_info.value.reason == "Username is not available"
