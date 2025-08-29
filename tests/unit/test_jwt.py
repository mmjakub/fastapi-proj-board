from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import joserfc
import pytest

from app import config, jwt
from app.endpoints.schema import OAuthTokenResponse
from app.errors import UnauthorizedError


@pytest.fixture()
def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def now_ts(now):
    return int(now.timestamp())


@pytest.fixture()
def username() -> str:
    return "user"


@pytest.fixture()
def token(username) -> OAuthTokenResponse:
    return jwt.create_access_token(username)


@pytest.fixture()
def jwt_key() -> joserfc.jwk.OctKey:
    return joserfc.jwk.OctKey.import_key(config.get_settings().jwt.secret_key)


@pytest.fixture()
def jwt_expires_sec() -> int:
    return config.get_settings().jwt.expires_minutes * 60


@pytest.fixture()
def jwt_algorithm() -> config.JwtAlg:
    return config.get_settings().jwt.algorithm


def test_token_has_correct_expires_value(token, jwt_expires_sec):
    assert token.expires == jwt_expires_sec


def test_token_has_correct_type(token):
    assert token.token_type == "Bearer"


def test_token_has_access_token_in_jwt_form(token):
    assert len(token.access_token.split(".")) == 3


def test_token_header_contains_correct_alg(token, jwt_key, jwt_algorithm):
    header = joserfc.jwt.decode(token.access_token, jwt_key).header
    assert header["alg"] == jwt_algorithm


def test_token_contains_correct_iat_claim(username, now, now_ts):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now
    token = jwt.create_access_token(username)

    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["iat"] == now_ts


def test_token_contains_correct_exp_claim(username, now):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now
    token = jwt.create_access_token(username)

    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["exp"] == int((now + timedelta(hours=1)).timestamp())


def test_token_contains_correct_sub_claim(token, username):
    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["sub"] == username


def test_username_can_be_extracted_from_valid_token(username, token):
    actual_username = jwt.get_username_from_jwt(token.access_token)
    assert actual_username == username


def test_expired_token_raises_unauthorized_error(username, now, jwt_expires_sec):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now - timedelta(seconds=jwt_expires_sec + 1)
        expired_token = jwt.create_access_token(username)
    with pytest.raises(UnauthorizedError):
        jwt.get_username_from_jwt(expired_token.access_token)


def test_token_with_invalid_signature_raises_unauthorized_error(username):
    token = jwt.create_access_token(username)
    with pytest.raises(UnauthorizedError):
        jwt.get_username_from_jwt(token.access_token[:-1])


def test_token_signed_with_different_key_raises_unauthorized_error(username):
    with patch.object(jwt, "jwt_key", joserfc.jwk.OctKey.import_key("foobar")):
        token = jwt.create_access_token(username)
    with pytest.raises(UnauthorizedError):
        jwt.get_username_from_jwt(token.access_token)


def test_create_token_with_mock_encode(username, now, jwt_algorithm, jwt_expires_sec, jwt_key):
    """
    This test is practically a copy of the implementation
    """
    header = {"alg": jwt_algorithm}
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(seconds=jwt_expires_sec),
    }

    with patch("app.jwt.datetime", **{"now.return_value": now}), patch(
        "app.jwt.jwt.encode", return_value="access_token"
    ) as mock:
        token = jwt.create_access_token(username)

    mock.assert_called_once_with(header, payload, jwt_key, [jwt_algorithm])
    assert token.access_token == "access_token"
    assert token.token_type == "Bearer"
    assert token.expires == jwt_expires_sec
