from typing import BinaryIO

from .errors import (
    CollaboratorConflict,
    ForbiddenError,
    ResourceNotFound,
    UsernameConflict,
)
from .models import Document, Project, User, Username
from .ports.repository import DataRepository, FileRepository
from .ports.gateway import PasswordHashGateway, TaskQueueGateway


def _raise_if_user_cannot_modify(user: Username, project: Project):
    if user != project.owner and user not in project.collaborators:
        raise ForbiddenError(
            "Only project owners and collaborators can access and modify projects"
        )


async def _get_project_if_user_is_collaborator(
    user: Username, project_id: int, repository: DataRepository, error_msg: str
) -> Project:
    project = await repository.get_project_by_id(project_id)
    if user not in project.collaborators:
        raise ForbiddenError(error_msg)
    return project


async def _get_project_if_user_is_owner(
    user: Username, project_id: int, repository: DataRepository, error_msg: str
) -> Project:
    project = await repository.get_project_by_id(project_id)
    if user != project.owner:
        raise ForbiddenError(error_msg)
    return project


async def create_project(
    user: Username, name: str, description: str, repository: DataRepository
) -> Project:
    project = await repository.create_project(
        owner=user, name=name, description=description
    )
    return project


async def list_projects(user: Username, repository: DataRepository) -> list[Project]:
    return await repository.get_all_projects_by_username(user)


async def get_project(
    user: Username, project_id: int, repository: DataRepository
) -> Project:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can view projects"
    )
    return project


async def update_project(
    user: Username,
    project_id: int,
    new_name: str,
    new_description: str,
    repository: DataRepository,
) -> Project:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can edit project info"
    )
    project.name = new_name
    project.description = new_description
    project = await repository.save_project(project)
    return project


async def delete_project(
    user: Username,
    project_id: int,
    data_repo: DataRepository,
    file_repo: FileRepository,
    tasks: TaskQueueGateway,
) -> None:
    project = await _get_project_if_user_is_owner(
        user, project_id, data_repo, "Only owner can delete projects"
    )
    await data_repo.delete_project(project)
    for doc in project.documents:
        tasks.add_task(file_repo.delete, doc.id)


async def list_project_documents(
    user: Username, project_id: int, repository: DataRepository
) -> list[Document]:
    project = await _get_project_if_user_is_collaborator(
        user, project_id, repository, "Only collaborators can edit project info"
    )
    return project.documents


async def add_user_to_project(
    user: Username, project_id: int, invitee: Username, repository: DataRepository
) -> None:
    project = await _get_project_if_user_is_owner(
        user, project_id, repository, "Only owner can add others"
    )
    if not await repository.user_exists(invitee):
        raise ResourceNotFound(f"<User:{invitee}> does not exist")
    if invitee in project.collaborators:
        raise CollaboratorConflict(
            f"<User:{invitee}> already collaborates on <Project:{project_id}>"
        )
    project.collaborators.add(invitee)
    await repository.save_project(project)


async def create_document(
    user: Username,
    project_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: DataRepository,
    file_repo: FileRepository,
) -> Document:
    await _get_project_if_user_is_collaborator(
        user,
        project_id,
        project_repo,
        "Only collaborators can upload project documents",
    )
    document = await project_repo.create_document(
        project_id=project_id, upload_filename=filename
    )
    # TODO: background file saving - need to consider business usecase - add status to documents
    await file_repo.save(document.id, file)
    return document


async def update_document(
    user: Username,
    document_id: int,
    filename: str,
    file: BinaryIO,
    project_repo: DataRepository,
    file_repo: FileRepository,
) -> Document:
    project = await project_repo.get_project_by_document_id(document_id)
    _raise_if_user_cannot_modify(user, project)
    # TODO: Could improve on this O(n) time if there are lots of documents in projects
    # and performance is bad, but seems that this is always dominated by O(n) when mapping to orm
    document = next(d for d in project.documents if d.id == document_id)
    if document.upload_filename != filename:
        document.upload_filename = filename
        await project_repo.save_project(project)

    # TODO: background file saving - need to consider business usecase - add status to documents
    await file_repo.save(document_id, file)
    return document


async def delete_document(
    user: Username,
    document_id: int,
    project_repo: DataRepository,
    file_repo: FileRepository,
    tasks: TaskQueueGateway,
) -> None:
    project = await project_repo.get_project_by_document_id(document_id)
    _raise_if_user_cannot_modify(user, project)
    document = next(d for d in project.documents if d.id == document_id)

    project.documents.remove(document)
    await project_repo.save_project(project)

    tasks.add_task(file_repo.delete, document_id)


async def download_document(
    user: Username,
    document_id: int,
    project_repo: DataRepository,
    file_repo: FileRepository,
) -> tuple[str, BinaryIO]:
    project = await project_repo.get_project_by_document_id(document_id)
    _raise_if_user_cannot_modify(user, project)
    document = next(d for d in project.documents if d.id == document_id)

    return document.upload_filename, await file_repo.get(document_id)


async def create_user(
    username: Username,
    password: str,
    repository: DataRepository,
    pw_hasher: PasswordHashGateway,
) -> User:
    if await repository.user_exists(username):
        raise UsernameConflict(f"Username '{username}' is not available")
    user = await repository.create_user(username, pw_hasher.hash(password))
    return user


async def verify_user_credentials(
    username: Username,
    password: str,
    repository: DataRepository,
    pw_hasher: PasswordHashGateway,
) -> bool:
    try:
        user = await repository.get_user(username)
        return pw_hasher.verify(password, user.password)
    except ResourceNotFound:
        return False
