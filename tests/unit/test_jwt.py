from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import joserfc
import pytest

from app import jwt
from app.errors import UnauthorizedError


@pytest.fixture()
def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def username() -> str:
    return "user"


def test_token_header_contains_correct_alg(username, now):
    token = jwt.create_access_token(username)

    header = joserfc.jwt.decode(token.access_token, jwt.jwt_key).header
    assert header["alg"] == jwt.jwt_settings.algorithm


def test_token_claims_contain_correct_sub(username, now):
    token = jwt.create_access_token(username)

    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["sub"] == username


def test_token_claims_contain_correct_iat(username, now):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now
    token = jwt.create_access_token(username)

    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["iat"] == int(now.timestamp())


def test_token_claims_contain_correct_exp(username, now):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now
    token = jwt.create_access_token(username)

    claims = joserfc.jwt.decode(token.access_token, jwt.jwt_key).claims
    assert claims["exp"] == int((now + timedelta(hours=1)).timestamp())


def test_expired_token_raises_unauthorized_error(username, now):
    with patch("app.jwt.datetime") as dt:
        dt.now.return_value = now - timedelta(minutes=jwt.jwt_settings.expires_minutes, seconds=1)
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
        jwt.get_username_from_jwt(token.access_token[:-1])
