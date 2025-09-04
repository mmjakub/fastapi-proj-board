import contextlib
import logging
import os
from typing import TypedDict, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from .adapters.local_file.repository import LocalFileRepository
from .adapters.s3.repository import S3FileRepository
from .adapters.sql_alchemy.orm import Base
from .config import get_settings
from .core.errors import ConflictError, ForbiddenError, ResourceNotFound
from .core.ports.repository import FileRepository
from .errors import OAuthException, UnauthorizedError
from .endpoints.auth import router as auth_router
from .endpoints.project import router as project_router
from .endpoints.document import router as document_router

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    session_factory: async_sessionmaker[AsyncSession]
    file_repository: FileRepository


async def init_postgres() -> async_sessionmaker[AsyncSession]:
    url = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_async_engine(url.format(**get_settings().pg.model_dump()))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine)


def init_file_service() -> FileRepository:
    s3_config = get_settings().s3
    if not s3_config.bucket:
        logger.info("Using local files for storage")
        return LocalFileRepository("document_files")
    else:
        logger.info(f"Using s3://{s3_config.bucket} for storage")

        kwargs = {}
        if endpoint_url := os.getenv("S3_ENDPOINT_URL"):
            logger.info(f"Using {endpoint_url} as s3 endpoint")
            kwargs["endpoint_url"] = endpoint_url

        return S3FileRepository(s3_config.bucket, **kwargs)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    session_factory = await init_postgres()
    file_repo = init_file_service()
    yield {
        "session_factory": session_factory,
        "file_repository": file_repo,
    }


app = FastAPI(lifespan=lifespan)


@app.exception_handler(OAuthException)
async def oauth_exception_handler(request: Request, exc: OAuthException):
    return JSONResponse(
        status_code=exc.status_code,
        content=dict(error=exc.error, error_description=exc.error_description),
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={"message": "Invalid JWT"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content={"error": exc.args[0]},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(
        status_code=403,
        content={"error": exc.args[0]},
    )


@app.exception_handler(ResourceNotFound)
async def not_found_handler(request: Request, exc: ResourceNotFound):
    return JSONResponse(
        status_code=404,
        content={"error": exc.args[0]},
    )


app.include_router(auth_router)
app.include_router(project_router)
app.include_router(document_router)
