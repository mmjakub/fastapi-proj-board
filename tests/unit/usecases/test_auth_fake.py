import pytest

from .fakes import FakeUserRepository, FakePasswordHashGateway
from app.core import services as sut
from app.core.errors import UsernameConflict


@pytest.fixture()
def pw_hasher() -> FakePasswordHashGateway:
    return FakePasswordHashGateway()


@pytest.fixture()
def test_user_credentials() -> tuple[str, str]:
    return "test_user", "test_password"


@pytest.fixture()
def user_repo_with_test_user(test_user_credentials) -> FakeUserRepository:
    return FakeUserRepository([test_user_credentials])


@pytest.fixture()
def empty_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


async def test_can_create_user_with_valid_input(test_user_credentials, empty_user_repo, pw_hasher):
    username, password = test_user_credentials

    user = await sut.create_user(username, password, empty_user_repo, pw_hasher)

    assert user.id == 1
    assert user.username == username
    assert user.password == password


async def test_cannot_create_user_with_existing_username(test_user_credentials, user_repo_with_test_user, pw_hasher):
    username, password = test_user_credentials

    with pytest.raises(UsernameConflict):
        await sut.create_user(username, password, user_repo_with_test_user, pw_hasher)


async def test_valid_credentials_can_be_verified(test_user_credentials, user_repo_with_test_user, pw_hasher):
    username, password = test_user_credentials

    success = await sut.verify_user_credentials(username, password, user_repo_with_test_user, pw_hasher)

    assert success


async def test_invalid_username_cannot_be_verified(test_user_credentials, empty_user_repo, pw_hasher):

    username, password = test_user_credentials

    success = await sut.verify_user_credentials(username, password, empty_user_repo, pw_hasher)

    assert not success


async def test_invalid_password_cannot_be_verified(test_user_credentials, user_repo_with_test_user, pw_hasher):
    username, _ = test_user_credentials
    wrong_password = "wrong"
    assert wrong_password != test_user_credentials[1]

    success = await sut.verify_user_credentials(username, wrong_password, user_repo_with_test_user, pw_hasher)

    assert not success
