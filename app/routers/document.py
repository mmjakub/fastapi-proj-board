import asyncio
from uuid import uuid4, UUID

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from ..dependencies import DBSessionDep, FileServiceDep
from ..jwt import JwtUsernameDep
from ..models import User, Document, Project

router = APIRouter(tags=["documents"])


class DocumentResponse(BaseModel):
    id: UUID
    filename: str

    @classmethod
    def from_sa_orm(cls, document: Document) -> "DocumentResponse":
        return cls(id=document.id, filename=document.filename)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_all_project_documents(
    project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep
) -> list[DocumentResponse]:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if project is None:
            raise HTTPException(status_code=404)
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)
        await project.awaitable_attrs.documents
        return [DocumentResponse.from_sa_orm(doc) for doc in project.documents]


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_file_to_project_documents(
    project_id: int,
    file: UploadFile,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> DocumentResponse:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if project is None:
            raise HTTPException(status_code=404)
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)
        document_id = uuid4()
        document = Document(id=document_id, filename=file.filename)
        document.project = project
        session.add(document)
        await file_service.save(document_id, file.file)
        await session.flush()
        return DocumentResponse.from_sa_orm(document)


@router.get("/documents/{document_id}")
async def download_document(
    document_id: UUID,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> StreamingResponse:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        document = await session.scalar(select(Document).where(Document.id == document_id))

        if document is None:
            raise HTTPException(status_code=404)

        project = await document.awaitable_attrs.project
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)

        file = await file_service.get(document_id)
        headers = {"Content-Disposition": f"attachment; filename={document.filename}"}
        return StreamingResponse(file, headers=headers, media_type="application/octet-stream")


@router.put("/documents/{document_id}")
async def update_document(
    document_id: UUID,
    file: UploadFile,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> DocumentResponse:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        document = await session.scalar(select(Document).where(Document.id == document_id))

        if document is None:
            raise HTTPException(status_code=404)

        project = await document.awaitable_attrs.project
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)

        await file_service.save(document_id, file.file)
        if file.filename:
            document.filename = file.filename
            await session.merge(document)
        return DocumentResponse.from_sa_orm(document)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
    file_service: FileServiceDep,
) -> None:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        document = await session.scalar(select(Document).where(Document.id == document_id))

        if document is None:
            raise HTTPException(status_code=404)

        project = await document.awaitable_attrs.project
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)

        await asyncio.gather(session.delete(document), file_service.delete(document_id))
