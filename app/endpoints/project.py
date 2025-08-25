from fastapi import APIRouter

from .dependencies import PagingDep
from .schema import ProjectInfo, ProjectResponse, error_responses, ErrorResponse, PagedList
from ..jwt import JwtUsernameDep

router = APIRouter(prefix="/projects", tags=["project"])


@router.post("/", status_code=201, summary="Create a project", responses={401: {"model": ErrorResponse}})
async def create(payload: ProjectInfo, username: JwtUsernameDep) -> ProjectResponse:
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
    raise NotImplementedError


@router.get("/", summary="List projects", responses={401: {"model": ErrorResponse}})
async def list_all(paging: PagingDep, username: JwtUsernameDep) -> PagedList[ProjectResponse]:
    """
    Returns a list of projects the current user can access.

    Optional query parameters
      - **page**: int = 0: page number, defaults to first page
      - **limit**: int = 20: items per page, defaults to 20


    Responses:
      - 200: Success
      - 401: Authentication required
    """
    raise NotImplementedError


@router.delete("/{project_id}", status_code=204, summary="Delete a project", responses=error_responses)
async def delete(project_id: int, username: JwtUsernameDep) -> None:
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
    raise NotImplementedError


@router.get("/{project_id}/info", summary="Get editable project info", responses=error_responses)
async def get(project_id: int, username: JwtUsernameDep) -> ProjectInfo:
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
    raise NotImplementedError


@router.put("/{project_id}/info", summary="Update project details", responses=error_responses)
async def update(project_id: int, project_info: ProjectInfo, username: JwtUsernameDep) -> ProjectInfo:
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
    raise NotImplementedError


@router.post(
    "/{project_id}/invite",
    responses={**error_responses, 409: {"model": ErrorResponse}},
    summary="Add a user to the project",
)
async def invite(project_id: int, user: str, username: JwtUsernameDep) -> None:
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
    raise NotImplementedError
