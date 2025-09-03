from unittest.mock import AsyncMock, Mock

import pytest

from app.core import services as sut
from app.core.errors import UsernameConflict, ResourceNotFound
from app.core.models import User
from app.core.ports.gateway import PasswordHashGateway
from app.core.ports.repository import DataRepository


async def test_can_create_user_with_valid_input():
    username = "username"
    password = "password"
    hashed_password = "hashed_password"

    mock_repo = AsyncMock(DataRepository)
    mock_repo.user_exists.return_value = False
    mock_repo.create_user.return_value = User(1, username, hashed_password)

    mock_pw_hasher = Mock(PasswordHashGateway)
    mock_pw_hasher.hash.return_value = hashed_password

    user = await sut.create_user(username, password, mock_repo, mock_pw_hasher)

    mock_repo.user_exists.assert_awaited_once_with(username)
    mock_pw_hasher.hash.assert_called_once_with(password)
    mock_repo.create_user.assert_awaited_once_with(username, hashed_password)
    assert user.id == 1
    assert user.username == username
    assert user.password == hashed_password


async def test_cannot_create_user_with_existing_username():
    username = "not_unique"

    mock_repo = AsyncMock(DataRepository)
    mock_repo.user_exists.return_value = True
    mock = Mock()

    with pytest.raises(UsernameConflict):
        await sut.create_user(username, mock, mock_repo, mock)
    mock_repo.user_exists.assert_called_once()


async def test_valid_credentials_can_be_verified():
    username = "username"
    password = "password"
    hashed_password = "hashed_password"

    mock_repo = AsyncMock(DataRepository)
    mock_repo.get_user.return_value = User(1, username, hashed_password)

    mock_pw_hasher = Mock(PasswordHashGateway)
    mock_pw_hasher.verify.return_value = True

    success = await sut.verify_user_credentials(
        username, password, mock_repo, mock_pw_hasher
    )

    assert success
    mock_repo.get_user.assert_called_once_with(username)
    mock_pw_hasher.verify.assert_called_once_with(password, hashed_password)


async def test_invalid_username_cannot_be_verified():
    username = "not_found"

    mock_repo = AsyncMock(DataRepository)
    mock_repo.get_user.side_effect = ResourceNotFound
    mock = Mock()

    success = await sut.verify_user_credentials(username, mock, mock_repo, mock)

    assert not success
    mock_repo.get_user.assert_called_once_with(username)


async def test_invalid_password_cannot_be_verified():
    username = "username"
    password = "invalid"
    hashed_password = "valid"

    mock_repo = AsyncMock(DataRepository)
    mock_repo.get_user.return_value = User(1, username, hashed_password)
    mock_pw_hasher = Mock(PasswordHashGateway)
    mock_pw_hasher.verify.return_value = False

    success = await sut.verify_user_credentials(
        username, password, mock_repo, mock_pw_hasher
    )

    assert not success
    mock_repo.get_user.assert_called_once_with(username)
    mock_pw_hasher.verify.assert_called_once_with(password, hashed_password)
