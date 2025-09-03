from typing import Annotated, TypedDict

from fastapi import Depends, Request
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.sql_alchemy.repository import SADataRepository
from app.core.ports.gateway import PasswordHashGateway
from app.core.ports.repository import DataRepository, FileRepository


class Paging(TypedDict):
    page: int
    limit: int


def get_paging_query_params(page: int = 0, limit: int = 0) -> Paging:
    return {"page": page, "limit": limit}


PagingDep = Annotated[Paging, Depends(get_paging_query_params)]


def get_session_factory(request: Request):
    return request.state.session_factory


async def get_data_repository(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    async with session_factory() as session, session.begin():
        yield SADataRepository(session)


DataRepositoryDep = Annotated[DataRepository, Depends(get_data_repository)]


def get_crypt_context():
    return CryptContext(schemes=["bcrypt"])


PasswordHashGatewayDep = Annotated[PasswordHashGateway, Depends(get_crypt_context)]


def get_file_repository(request: Request):
    return request.state.file_repository


FileRepositoryDep = Annotated[FileRepository, Depends(get_file_repository)]
