from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .schema import OAuthErrorResponse, RegisterUserRequest, UserResponse, ErrorResponse
from .dependencies import DataRepositoryDep, PasswordHashGatewayDep
from ..core.services import create_user, verify_user_credentials
from ..errors import InvalidGrantException
from ..jwt import OAuthTokenResponse, create_access_token

router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    summary="Sign In",
    responses={400: {"model": OAuthErrorResponse}},
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    repository: DataRepositoryDep,
    pw_hasher: PasswordHashGatewayDep,
) -> OAuthTokenResponse:
    """
    Exchange **username** and **password** for an access token using OAuth2 password grant.

    Request form:
    - **username**: required
    - **password**: required

    Responses:
    - 200: Success
    - 400: Invalid request or credentials
    """
    if not await verify_user_credentials(
        form_data.username, form_data.password, repository, pw_hasher
    ):
        raise InvalidGrantException
    return create_access_token(form_data.username)


@router.post(
    "/register",
    summary="Sign Up for the app",
    responses={409: {"model": ErrorResponse}},
    status_code=201,
)
async def register(
    payload: RegisterUserRequest,
    repository: DataRepositoryDep,
    pw_hasher: PasswordHashGatewayDep,
) -> UserResponse:
    """
    Register a new user by providing credentials:

    Request body:
    - **username**: must be unique
    - **password**: required

    Responses:
    - 201: User created
    - 409: Conflict (username already exists)
    - 422: Validation error
    """
    user = await create_user(payload.username, payload.password, repository, pw_hasher)
    return UserResponse(username=user.username, owned_projects=[], projects=[])
