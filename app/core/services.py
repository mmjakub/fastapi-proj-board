import asyncio
from typing import BinaryIO

from .errors import CollaboratorConflict, ForbiddenError, ResourceNotFound, UsernameConflict
from .models import Document, Project, User
from .ports.repository import DocumentRepository, ProjectRepository, UserRepository
from .ports.service import FileService, SupportsHashing


async def _get_project_if_user_is_collaborator(
    username: str, project_id: int, repository: ProjectRepository, error_msg: str
) -> Project:
    project = await repository.get(project_id)
    if username not in project.collaborators:
        raise ForbiddenError(error_msg)
    return project


async def _get_project_if_user_is_owner(
    username: str, project_id: int, repository: ProjectRepository, error_msg: str
) -> Project:
    project = await repository.get(project_id)
    if username != project.owner:
        raise ForbiddenError(error_msg)
    return project


async def _delete_document(document: Document, repository: DocumentRepository, file_service: FileService) -> None:
    await asyncio.gather(repository.delete(document), file_service.delete(document.id))  # type: ignore


async def create_project(username: str, name: str, description: str, repository: ProjectRepository) -> Project:
    project = Project(
        id=None,
        name=name,
        description=description,
        owner=username,
        collaborators={username},
        documents=[],
    )
    project = await repository.save(project)
    return project


async def list_projects(username: str, repository: ProjectRepository) -> list[Project]:
    return await repository.get_all(username)


async def get_project(username: str, project_id: int, repository: ProjectRepository) -> Project:
    project = await _get_project_if_user_is_collaborator(
        username, project_id, repository, "Only collaborators can view projects"
    )
    return project


async def update_project(
    username: str, project_id: int, new_name: str, new_description: str, repository: ProjectRepository
) -> Project:
    project = await _get_project_if_user_is_collaborator(
        username, project_id, repository, "Only collaborators can edit project info"
    )
    project.name = new_name
    project.description = new_description
    project = await repository.save(project)
    return project


async def delete_project(
    username: str,
    project_id: int,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_service: FileService,
) -> None:
    project = await _get_project_if_user_is_owner(username, project_id, project_repo, "Only owner can delete projects")
    await asyncio.gather(
        *(_delete_document(d, document_repo, file_service) for d in project.documents),
        project_repo.delete(project),
    )


async def list_project_documents(username: str, project_id: int, repository: ProjectRepository) -> list[Document]:
    project = await _get_project_if_user_is_collaborator(
        username, project_id, repository, "Only collaborators can edit project info"
    )
    return project.documents


async def add_user_to_project(
    username: str, project_id: int, invitee_username: str, project_repo: ProjectRepository, user_repo: UserRepository
) -> None:
    project = await _get_project_if_user_is_owner(username, project_id, project_repo, "Only owner can add others")
    if not await user_repo.exists(invitee_username):
        raise ResourceNotFound(f"<User:{invitee_username}> does not exist")
    if invitee_username in project.collaborators:
        raise CollaboratorConflict(f"<User:{invitee_username}> already colaborates on <Project:{project_id}>")
    project.collaborators.add(invitee_username)
    await project_repo.save(project)


async def create_document(
    username: str,
    project_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_service: FileService,
) -> Document:
    await _get_project_if_user_is_collaborator(
        username, project_id, project_repo, "Only collaborators can upload project documents"
    )
    # id is None, because dbms will generate it
    document = Document(id=None, project_id=project_id, upload_filename=filename)
    document = await document_repo.save(document)
    # id: int | None causes problems here
    await file_service.save(document.id, file)  # type: ignore
    return document


async def update_document(
    username: str,
    document_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_service: FileService,
) -> Document:
    document = await document_repo.get(document_id)
    await _get_project_if_user_is_collaborator(
        username, document.project_id, project_repo, "Only collaborators can edit project documents"
    )
    if document.upload_filename != filename:
        document.upload_filename = filename
        document = await document_repo.save(document)
    await file_service.save(document_id, file)
    return document


async def delete_document(
    username: str,
    document_id: int,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_service: FileService,
) -> None:
    document = await document_repo.get(document_id)
    await _get_project_if_user_is_collaborator(
        username, document.project_id, project_repo, "Only collaborators can delete project documents"
    )
    await _delete_document(document, document_repo, file_service)


async def create_user(username: str, password: str, repository: UserRepository, hash_service: SupportsHashing) -> User:
    if await repository.exists(username):
        raise UsernameConflict("Username 'username' is not available")
    user = await repository.create(username, password=hash_service.hash(password))
    return user


async def verify_user_credentials(
    username: str, password: str, repository: UserRepository, hash_service: SupportsHashing
) -> bool:
    user = await repository.get_or_none(username)
    return user is not None and hash_service.verify(password, user.password)
