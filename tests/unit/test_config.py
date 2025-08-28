from unittest.mock import patch

from pydantic import ValidationError
import pytest

from app.config import Settings, JwtAlg


@pytest.fixture()
def test_value() -> str:
    return "42"


def test_jwt_secret_key_is_mandatory():
    with patch.dict("os.environ", {}, True), pytest.raises(ValidationError):
        Settings()


def test_jwt_secret_key_can_be_set(test_value):
    with patch.dict("os.environ", {"JWT_SECRET_KEY": test_value}):
        settings = Settings()
    assert settings.jwt.secret_key == test_value


def test_jwt_expiration_time_in_minutes_can_be_set():
    with patch.dict("os.environ", {"JWT_EXPIRES_MINUTES": "42"}):
        settings = Settings()
    assert settings.jwt.expires_minutes == 42


def test_jwt_expiration_time_in_minutes_is_60_by_default():
    settings = Settings()
    assert settings.jwt.expires_minutes == 60


def test_jwt_algorithm_can_be_set():
    with patch.dict("os.environ", {"JWT_ALGORITHM": JwtAlg.HS256}):
        settings = Settings()
    assert settings.jwt.algorithm == JwtAlg.HS256


def test_jwt_algorithm_is_HS256_by_default():
    settings = Settings()
    assert settings.jwt.algorithm == JwtAlg.HS256


def test_jwt_algorithm_cannot_be_set_outside_predefined_values(test_value):
    with patch.dict("os.environ", {"JWT_ALGORITHM": test_value}), pytest.raises(ValidationError):
        Settings()
