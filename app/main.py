import contextlib
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .config import settings
from .models import Base
from .errors import OAuthException, UnauthorizedError, UsernameTaken
from .file_service import FileService, S3FileService, LocalFileService
from .routers.auth import router as auth_router
from .routers.project import router as project_router
from .routers.document import router as document_router


class State(TypedDict):
    DBSession: async_sessionmaker[AsyncSession]
    file_service: FileService


async def init_db() -> async_sessionmaker[AsyncSession]:
    url = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_async_engine(url.format(**settings.pg.model_dump()))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine)
    return Session


def init_file_service() -> FileService:
    bucket = settings.s3.bucket
    if not bucket:
        return LocalFileService()
    else:
        return S3FileService(bucket)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    DBSession = await init_db()
    file_service = init_file_service()
    yield {
        "DBSession": DBSession,
        "file_service": file_service,
    }


app = FastAPI(lifespan=lifespan)


@app.exception_handler(OAuthException)
async def oauth_exception_handler(request: Request, exc: OAuthException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.content(),
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={"error": "Invalid JWT"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(UsernameTaken)
async def username_taken_handler(request: Request, exc: UsernameTaken):
    return JSONResponse(
        status_code=400,
        content={"error": "Username is not available"},
    )


app.include_router(auth_router)
app.include_router(project_router)
app.include_router(document_router)
