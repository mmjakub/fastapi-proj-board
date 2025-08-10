from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .file_service import FileService


def get_db_session(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.state.DBSession


DBSessionDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_db_session)]


def get_file_service(request: Request) -> FileService:
    return request.state.file_service


FileServiceDep = Annotated[FileService, Depends(get_file_service)]
