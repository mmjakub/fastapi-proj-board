import pytest

from app.core import services as sut
from app.core.errors import UsernameConflict
from .fakes import FakePasswordHashGateway, FakeDataRepository


@pytest.fixture()
def pw_hasher() -> FakePasswordHashGateway:
    return FakePasswordHashGateway()


@pytest.fixture()
def test_user_credentials() -> tuple[str, str]:
    return "test_user", "test_user"


@pytest.fixture()
def repository_with_test_user(test_user_credentials) -> FakeDataRepository:
    repo = FakeDataRepository(setup_user=[test_user_credentials[0]])
    return repo


@pytest.fixture()
def repository() -> FakeDataRepository:
    return FakeDataRepository()


async def test_can_create_user_with_valid_input(
    test_user_credentials, repository, pw_hasher
):
    username, password = test_user_credentials
    repository.setup_id(1)

    user = await sut.create_user(username, password, repository, pw_hasher)

    assert user.id == 1
    assert user.username == username
    assert user.password == password


async def test_cannot_create_user_with_existing_username(
    test_user_credentials, repository_with_test_user, pw_hasher
):
    username, password = test_user_credentials

    with pytest.raises(UsernameConflict):
        await sut.create_user(username, password, repository_with_test_user, pw_hasher)


async def test_valid_credentials_can_be_verified(
    test_user_credentials, repository_with_test_user, pw_hasher
):
    username, password = test_user_credentials

    success = await sut.verify_user_credentials(
        username, password, repository_with_test_user, pw_hasher
    )

    assert success


async def test_invalid_username_cannot_be_verified(
    test_user_credentials, repository, pw_hasher
):

    username, password = test_user_credentials

    success = await sut.verify_user_credentials(
        username, password, repository, pw_hasher
    )

    assert not success


async def test_invalid_password_cannot_be_verified(
    test_user_credentials, repository_with_test_user, pw_hasher
):
    username, _ = test_user_credentials
    wrong_password = "wrong"
    assert wrong_password != test_user_credentials[1]

    success = await sut.verify_user_credentials(
        username, wrong_password, repository_with_test_user, pw_hasher
    )

    assert not success
