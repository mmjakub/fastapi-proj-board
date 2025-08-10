import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from ..dependencies import DBSessionDep
from ..errors import InvalidGrantException, UsernameTaken
from ..jwt import create_access_token, Token, JwtUsernameDep
from ..models import User

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    DBSession: DBSessionDep,
) -> Token:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == form_data.username))).one_or_none()
        if user is None or not pwd_context.verify(form_data.password, user.password):
            raise InvalidGrantException()
    return create_access_token(form_data.username)


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
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()

        owned_projects, projects = await asyncio.gather(
            user.awaitable_attrs.owned_projects, user.awaitable_attrs.projects
        )

        return UserResponse(
            username=username,
            owned_projects=[p.id for p in owned_projects],
            projects=[p.id for p in projects],
        )


@router.post("/register", status_code=201)
async def register(payload: RegisterUserRequest, DBSession: DBSessionDep) -> UserResponse:
    hashed_password = pwd_context.hash(payload.password)
    async with DBSession() as session, session.begin():
        user = User(username=payload.username, password=hashed_password)
        session.add(user)
        try:
            await session.flush()
        except IntegrityError:
            raise UsernameTaken()
    return UserResponse(username=payload.username)
