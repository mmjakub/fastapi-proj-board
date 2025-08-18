from uuid import UUID

from fastapi import APIRouter, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..dependencies import DBSessionDep, FileServiceDep
from ..jwt import JwtUsernameDep
from .. import transaction_script as ts

router = APIRouter(tags=["documents"])


class DocumentResponse(BaseModel):
    id: UUID
    filename: str


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_all_project_documents(
    project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep
) -> list[DocumentResponse]:
    documents = await ts.get_proj_documents(project_id, username, DBSession)
    return [DocumentResponse(**doc) for doc in documents]


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_file_to_project_documents(
    project_id: int,
    file: UploadFile,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> DocumentResponse:
    async with DBSession() as session, session.begin():
        document = await ts.upload_document_to_proj(
            project_id,
            username,
            DBSession,
            file.file,
            file.filename or "",
            file_service,
        )
        return DocumentResponse(**document)


@router.get("/documents/{document_id}")
async def download_document(
    document_id: UUID,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> StreamingResponse:
    file, filename = await ts.download_document(document_id, username, DBSession, file_service)
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(file, headers=headers, media_type="application/octet-stream")


@router.put("/documents/{document_id}")
async def update_document(
    document_id: UUID,
    file: UploadFile,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> DocumentResponse:
    document = await ts.update_document(
        document_id,
        username,
        DBSession,
        file.file,
        file.filename,
        file_service,
    )
    return DocumentResponse(**document)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> None:
    async with DBSession() as session, session.begin():
        await ts.delete_document(document_id, username, DBSession, file_service)
