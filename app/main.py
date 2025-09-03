from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .core.errors import ConflictError, ForbiddenError, ResourceNotFound
from .errors import OAuthException, UnauthorizedError
from .endpoints.auth import router as auth_router
from .endpoints.project import router as project_router
from .endpoints.document import router as document_router


app = FastAPI()


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
async def forbidden_handler(request: Request, exc: ResourceNotFound):
    return JSONResponse(
        status_code=404,
        content={"error": exc.args[0]},
    )


app.include_router(auth_router)
app.include_router(project_router)
app.include_router(document_router)
