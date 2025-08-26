from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .schema import OAuthErrorResponse, RegisterUserRequest, UserResponse, ErrorResponse
from ..jwt import OAuthTokenResponse

router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    summary="Sign In",
    responses={400: {"model": OAuthErrorResponse}},
)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> OAuthTokenResponse:
    """
    Exchange **username** and **password** for an access token using OAuth2 password grant.

    Request form:
    - **username**: required
    - **password**: required

    Responses:
    - 200: Success
    - 400: Invalid request or credentials
    """
    raise NotImplementedError


@router.post(
    "/register",
    summary="Sign Up for the app",
    responses={409: {"model": ErrorResponse}},
    status_code=201,
)
async def register(payload: RegisterUserRequest) -> UserResponse:
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
    raise NotImplementedError
