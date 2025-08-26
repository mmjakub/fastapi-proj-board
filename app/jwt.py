from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.jwk import OctKey

from .config import settings
from .errors import UnauthorizedError
from .endpoints.schema import OAuthTokenResponse


jwt_settings = settings.jwt
jwt_key = OctKey.import_key(jwt_settings.secret_key)


def create_access_token(username: str) -> OAuthTokenResponse:
    header = {"alg": jwt_settings.algorithm}
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=jwt_settings.expires_minutes),
    }
    access_token = jwt.encode(header, payload, jwt_key, [jwt_settings.algorithm])
    return OAuthTokenResponse(access_token=access_token, token_type="Bearer", expires=jwt_settings.expires_minutes * 60)


def get_sub_from_jwt(token: str) -> str:
    decoded_token = jwt.decode(token, jwt_key, [jwt_settings.algorithm])
    return decoded_token.claims["sub"]


async def get_username_from_jwt(
    token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="/login"))],
) -> str:
    try:
        username = get_sub_from_jwt(token)
    except Exception:
        raise UnauthorizedError()
    return username


JwtUsernameDep = Annotated[str, Depends(get_username_from_jwt)]
