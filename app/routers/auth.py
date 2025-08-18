from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..dependencies import DBSessionDep
from ..jwt import Token, JwtUsernameDep
from .. import transaction_script as ts

router = APIRouter()


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    DBSession: DBSessionDep,
) -> Token:
    return await ts.login(form_data.username, form_data.password, DBSession)


class RegisterUserRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    owned_projects: list[int] = []
    projects: list[int] = []


@router.get("/me")
async def get_authorized_user(
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
) -> UserResponse:
    username, owned_projects, projects = await ts.me(username, DBSession)
    return UserResponse(
        username=username,
        owned_projects=owned_projects,
        projects=projects,
    )


@router.post("/register", status_code=201)
async def register(payload: RegisterUserRequest, DBSession: DBSessionDep) -> UserResponse:
    username = await ts.register(payload.username, payload.password, DBSession)
    return UserResponse(username=username)
