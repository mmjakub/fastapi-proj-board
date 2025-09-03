from fastapi import APIRouter, BackgroundTasks

from .dependencies import PagingDep, DataRepositoryDep, FileRepositoryDep
from .document import make_document_response
from .schema import (
    ProjectInfo,
    ProjectResponse,
    error_responses,
    ErrorResponse,
    PagedList,
    PageInfo,
)
from ..core.models import Project
from ..jwt import JwtUsernameDep
from ..core.services import (
    list_projects,
    delete_project,
    create_project,
    get_project,
    update_project,
    add_user_to_project,
)


def make_project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        info=ProjectInfo(name=project.name, description=project.description),
        documents=[make_document_response(d) for d in project.documents],
        owner=project.owner,
    )


router = APIRouter(prefix="/projects", tags=["project"])


@router.post(
    "/",
    status_code=201,
    summary="Create a project",
    responses={401: {"model": ErrorResponse}},
)
async def create(
    payload: ProjectInfo, username: JwtUsernameDep, repository: DataRepositoryDep
) -> ProjectResponse:
    """
    Create a new project owned by the authenticated user with provided details.

    Request body:
      - name (str): Project name
      - description (str): Project description

    Responses:
      - 201: Project created
      - 401: Authentication required
      - 422: Invalid input
    """
    project = await create_project(
        username, payload.name, payload.description, repository
    )
    return make_project_response(project)


@router.get("/", summary="List projects", responses={401: {"model": ErrorResponse}})
async def list_all(
    paging: PagingDep, username: JwtUsernameDep, repository: DataRepositoryDep
) -> PagedList[ProjectResponse]:
    """
    Returns a list of projects the current user can access.

    Optional query parameters
      - **page**: int = 0: page number, defaults to first page
      - **limit**: int = 20: items per page, defaults to 20


    Responses:
      - 200: Success
      - 401: Authentication required
    """
    projects = await list_projects(username, repository)
    # TODO: real repository-based paging
    return PagedList(
        items=[make_project_response(p) for p in projects],
        page=PageInfo(
            page_index=0,
            page_size=len(projects),
            total_pages=1,
            total_elements=len(projects),
        ),
    )


@router.delete(
    "/{project_id}",
    status_code=204,
    summary="Delete a project",
    responses=error_responses,
)
async def delete(
    project_id: int,
    username: JwtUsernameDep,
    data_repo: DataRepositoryDep,
    file_repo: FileRepositoryDep,
    tasks: BackgroundTasks,
) -> None:
    """
    Permanently delete the specified project

    Path parameters:
      - project_id (int): Identifier of the project

    Responses:
      - 204: Deleted successfully
      - 401: Authentication required
      - 403: Not authorized to delete this project
      - 404: Project not found
    """
    await delete_project(username, project_id, data_repo, file_repo, tasks)


@router.get(
    "/{project_id}/info", summary="Get editable project info", responses=error_responses
)
async def get(
    project_id: int, username: JwtUsernameDep, repository: DataRepositoryDep
) -> ProjectInfo:
    """
    Returns the project's editable info for the given project id.

    Path parameters:
      - project_id (int): Identifier of the project

    Responses:
      - 200: Success
      - 401: Authentication required
      - 403: Insufficient permissions to view this project
      - 404: Project not found
    """
    project = await get_project(username, project_id, repository)
    return ProjectInfo(name=project.name, description=project.description)


@router.put(
    "/{project_id}/info", summary="Update project details", responses=error_responses
)
async def update(
    project_id: int,
    project_info: ProjectInfo,
    username: JwtUsernameDep,
    repository: DataRepositoryDep,
) -> ProjectInfo:
    """
    Update project information.

    Path parameters:
      - project_id (int): Identifier of the project

    Request body:
      - name (str): New project name
      - description (str): New description

    Responses:
      - 200: Updated info returned
      - 401: Authentication required
      - 403: Insufficient permissions to modify this project
      - 404: Project not found
      - 422: Invalid input

    TODO:
    - Consider what should happen when concurrent edits occur (would require some versioning solution)
    - Simples solution could be ETags with hashed name+description
    """
    project = await update_project(
        username, project_id, project_info.name, project_info.description, repository
    )
    return ProjectInfo(name=project.name, description=project.description)


@router.post(
    "/{project_id}/invite",
    responses={**error_responses, 409: {"model": ErrorResponse}},
    summary="Add a user to the project",
)
async def invite(
    project_id: int, user: str, username: JwtUsernameDep, repository: DataRepositoryDep
) -> None:
    """
    Adds a user to the project by username.

    Path parameters:
      - project_id (int): Identifier of the project

    Query parameters:
      - user (str): Username of the invitee

    Responses:
      - 200: User succesfully added to project
      - 401: Authentication required
      - 403: Not authorized to invite users
      - 404: Project or invitee not found
      - 409: Invitee already is a member of this project
    """
    await add_user_to_project(username, project_id, user, repository)
