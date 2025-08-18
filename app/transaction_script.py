import asyncio
from typing import TypedDict, BinaryIO
from uuid import UUID, uuid4

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from .errors import (
    DomainError,
    ForbiddenError,
    InvalidGrantException,
    UsernameTaken,
    ProjectNotFound,
    UserNotFound,
    DocumentNotFound,
)
from .file_service import FileService
from .jwt import Token, create_access_token
from .models import Document, User, Project


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def _get_user(username: str, session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.username == username))
    if user is None:
        raise UserNotFound(resource=username)
    return user


async def _get_project(project_id: int, session: AsyncSession) -> Project:
    project = await session.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise ProjectNotFound(resource=project_id)
    return project


async def _get_project_if_owner(project_id: int, username: str, session: AsyncSession) -> Project:
    user = await _get_user(username, session)
    project = await _get_project(project_id, session)

    if user is not await project.awaitable_attrs.owner:
        raise ForbiddenError(reason="Must be project owner to do this")

    return project


async def _get_project_if_colab(project_id: int, username: str, session: AsyncSession) -> Project:
    user = await _get_user(username, session)
    project = await _get_project(project_id, session)

    if user not in await project.awaitable_attrs.collaborators:
        raise ForbiddenError(reason="Must be project collaborator to do this")

    return project


async def _get_document(document_id: UUID, username: str, session: AsyncSession) -> Document:
    document = await session.scalar(select(Document).where(Document.id == document_id))

    if document is None:
        raise DocumentNotFound(resource=document_id)

    await _get_project_if_colab(document.project_id, username, session)

    return document


async def login(
    username: str,
    password: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> Token:
    async with session_factory() as session, session.begin():
        user = await _get_user(username, session)
        if user is None or not pwd_context.verify(password, user.password):
            raise InvalidGrantException()
    return create_access_token(username)


async def register(
    username: str,
    password: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> str:
    hashed_password = pwd_context.hash(password)
    async with session_factory() as session, session.begin():
        user = User(username=username, password=hashed_password)
        session.add(user)
        try:
            await session.flush()
        except IntegrityError:
            raise UsernameTaken()
        return user.username


async def me(
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[str, list[int], list[int]]:
    async with session_factory() as session, session.begin():
        user = await _get_user(username, session)
        owned_projects, projects = await asyncio.gather(
            user.awaitable_attrs.owned_projects, user.awaitable_attrs.projects
        )
        return user.username, [p.id for p in owned_projects], [p.id for p in projects]


class DocumentDto(TypedDict):
    id: UUID
    filename: str


class ProjectInfoDto(TypedDict):
    name: str
    description: str


class ProjectDto(TypedDict):
    id: int
    info: ProjectInfoDto
    documents: list[DocumentDto]
    owner: str


def document_to_dto(document: Document) -> DocumentDto:
    return DocumentDto(id=document.id, filename=document.filename)


async def project_to_dto(project: Project) -> ProjectDto:
    return ProjectDto(
        id=project.id,
        owner=(await project.awaitable_attrs.owner).username,
        info=ProjectInfoDto(name=project.name, description=project.description),
        documents=[document_to_dto(doc) for doc in await project.awaitable_attrs.documents],
    )


async def create_project(
    owner: str,
    name: str,
    description: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> ProjectDto:
    async with session_factory() as session, session.begin():
        user = await _get_user(owner, session)
        project = Project(
            owner=user,
            name=name,
            description=description,
            collaborators=[user],
            documents=[],
        )
        session.add(project)
        await session.flush()
        return await project_to_dto(project)


async def list_projects(
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> list[ProjectDto]:
    async with session_factory() as session, session.begin():
        user = await _get_user(username, session)
        return [await project_to_dto(proj) for proj in await user.awaitable_attrs.projects]


async def delete_project(
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
    file_service: FileService,
) -> None:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_owner(project_id, username, session)

        documents = await project.awaitable_attrs.documents
        await asyncio.gather(
            *(file_service.delete(doc.id) for doc in documents),
            session.delete(project),
        )


async def get_project_info(
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> ProjectInfoDto:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_colab(project_id, username, session)
        return ProjectInfoDto(name=project.name, description=project.description)


async def change_project_info(
    name: str,
    description: str,
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> ProjectInfoDto:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_colab(project_id, username, session)

        project.name = name
        project.description = description
        await session.merge(project)

        return ProjectInfoDto(name=project.name, description=project.description)


async def invite_user(
    invited_username: str,
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_owner(project_id, username, session)

        invited_user = await _get_user(invited_username, session)

        if invited_user in await project.awaitable_attrs.collaborators:
            raise DomainError(f"User ${invited_user.username} already collaborates on this project")

        project.collaborators.append(invited_user)
        await session.merge(project)


async def get_proj_documents(
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> list[DocumentDto]:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_colab(project_id, username, session)
        documents = await project.awaitable_attrs.documents
        return [DocumentDto(id=doc.id, filename=doc.filename) for doc in documents]


async def upload_document_to_proj(
    project_id: int,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
    file: BinaryIO,
    filename: str,
    file_service: FileService,
) -> DocumentDto:
    async with session_factory() as session, session.begin():
        project = await _get_project_if_colab(project_id, username, session)
        document = Document(id=uuid4(), filename=filename)
        document.project = project
        session.add(document)

        await asyncio.gather(
            session.flush(),
            file_service.save(document.id, file),
        )

        return DocumentDto(id=document.id, filename=document.filename)


async def download_document(
    document_id: UUID,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
    file_service: FileService,
) -> tuple[BinaryIO, str]:
    async with session_factory() as session, session.begin():
        document = await _get_document(document_id, username, session)
        return await file_service.get(document_id), document.filename


async def update_document(
    document_id: UUID,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
    file: BinaryIO,
    filename: str | None,
    file_service: FileService,
) -> DocumentDto:
    async with session_factory() as session, session.begin():
        document = await _get_document(document_id, username, session)
        if filename is not None and filename != document.filename:
            document.filename = filename
            await session.merge(document)
        await file_service.save(document_id, file)
        return DocumentDto(id=document.id, filename=document.filename)


async def delete_document(
    document_id: UUID,
    username: str,
    session_factory: async_sessionmaker[AsyncSession],
    file_service: FileService,
) -> None:
    async with session_factory() as session, session.begin():
        document = await _get_document(document_id, username, session)
        await asyncio.gather(file_service.delete(document.id), session.delete(document))
