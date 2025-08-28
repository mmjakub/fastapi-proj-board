import asyncio
from typing import BinaryIO

from .errors import CollaboratorConflict, ForbiddenError, ResourceNotFound, UsernameConflict
from .models import Document, Project, User, Username
from .ports.repository import DocumentRepository, ProjectRepository, UserRepository, FileRepository
from .ports.gateway import PasswordHashGateway, TaskQueueGateway


async def _get_project_if_user_is_collaborator(
    user: Username, project_id: int, repository: ProjectRepository, error_msg: str
) -> Project:
    project = await repository.get(project_id)
    if user not in project.collaborators:
        raise ForbiddenError(error_msg)
    return project


async def _get_project_if_user_is_owner(
    user: Username, project_id: int, repository: ProjectRepository, error_msg: str
) -> Project:
    project = await repository.get(project_id)
    if user != project.owner:
        raise ForbiddenError(error_msg)
    return project


async def _delete_document(
    document: Document, document_repo: DocumentRepository, file_repo: FileRepository, task_queue: TaskQueueGateway
) -> None:
    await document_repo.delete(document)
    if document.id is None:
        raise RuntimeError("Document has no id")
    task_queue.add_task(file_repo.delete, document.id)


async def create_project(user: Username, name: str, description: str, repository: ProjectRepository) -> Project:
    project = Project(
        id=None,
        name=name,
        description=description,
        owner=user,
        collaborators={user},
        documents=[],
    )
    project = await repository.save(project)
    return project


async def list_projects(user: Username, repository: ProjectRepository) -> list[Project]:
    return await repository.get_all(user)


async def get_project(user: Username, project_id: int, repository: ProjectRepository) -> Project:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can view projects"
    )
    return project


async def update_project(
    user: Username, project_id: int, new_name: str, new_description: str, repository: ProjectRepository
) -> Project:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can edit project info"
    )
    project.name = new_name
    project.description = new_description
    project = await repository.save(project)
    return project


async def delete_project(
    user: Username,
    project_id: int,
    project_repo: ProjectRepository,
    doc_repo: DocumentRepository,
    file_repo: FileRepository,
    tasks: TaskQueueGateway,
) -> None:
    project = await _get_project_if_user_is_owner(user, project_id, project_repo, "Only owner can delete projects")
    await asyncio.gather(
        *(_delete_document(d, doc_repo, file_repo, tasks) for d in project.documents),
        project_repo.delete(project),
    )


async def list_project_documents(user: Username, project_id: int, repository: ProjectRepository) -> list[Document]:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can edit project info"
    )
    return project.documents


async def add_user_to_project(
    user: Username, project_id: int, invitee: Username, project_repo: ProjectRepository, user_repo: UserRepository
) -> None:
    project = await _get_project_if_user_is_owner(user, project_id, project_repo, "Only owner can add others")
    if not await user_repo.exists(invitee):
        raise ResourceNotFound(f"<User:{invitee}> does not exist")
    if invitee in project.collaborators:
        raise CollaboratorConflict(f"<User:{invitee}> already colaborates on <Project:{project_id}>")
    project.collaborators.add(invitee)
    await project_repo.save(project)


async def create_document(
    user: Username,
    project_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_repo: FileRepository,
) -> Document:
    await _get_project_if_user_is_collaborator(
        user, project_id, project_repo, "Only collaborators can upload project documents"
    )
    # id is None, because dbms will generate it
    document = Document(id=None, project_id=project_id, upload_filename=filename)
    document = await document_repo.save(document)
    if document.id is None:
        raise RuntimeError("Document has no id")
    # TODO: background file saving - need to consider business usecase - add status to documents
    await file_repo.save(document.id, file)
    return document


async def update_document(
    user: Username,
    document_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_service: FileRepository,
) -> Document:
    document = await document_repo.get(document_id)
    await _get_project_if_user_is_collaborator(
        user, document.project_id, project_repo, "Only collaborators can edit project documents"
    )
    if document.upload_filename != filename:
        document.upload_filename = filename
        document = await document_repo.save(document)
    # TODO: background file saving - need to consider business usecase - add status to documents
    await file_service.save(document_id, file)
    return document


async def delete_document(
    user: Username,
    document_id: int,
    project_repo: ProjectRepository,
    document_repo: DocumentRepository,
    file_repo: FileRepository,
    tasks: TaskQueueGateway,
) -> None:
    document = await document_repo.get(document_id)
    await _get_project_if_user_is_collaborator(
        user, document.project_id, project_repo, "Only collaborators can delete project documents"
    )
    await _delete_document(document, document_repo, file_repo, tasks)


async def create_user(
    username: Username, password: str, repository: UserRepository, pw_hasher: PasswordHashGateway
) -> User:
    if await repository.exists(username):
        raise UsernameConflict("Username 'username' is not available")
    user = await repository.create(username, password=pw_hasher.hash(password))
    return user


async def verify_user_credentials(
    username: Username, password: str, repository: UserRepository, pw_hasher: PasswordHashGateway
) -> bool:
    user = await repository.get_or_none(username)
    return user is not None and pw_hasher.verify(password, user.password)
