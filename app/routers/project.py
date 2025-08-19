from fastapi import APIRouter
from pydantic import BaseModel

from .document import DocumentResponse
from ..dependencies import DBSessionDep, FileServiceDep
from ..jwt import JwtUsernameDep
from .. import transaction_script as ts

router = APIRouter(prefix="/projects", tags=["project"])


class ProjectInfo(BaseModel):
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    info: ProjectInfo
    documents: list[DocumentResponse]
    owner: str

    @staticmethod
    def from_dto(dto: ts.ProjectDto) -> "ProjectResponse":
        return ProjectResponse(
            id=dto["id"],
            info=ProjectInfo(**dto["info"]),
            documents=[DocumentResponse(**doc) for doc in dto["documents"]],
            owner=dto["owner"],
        )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectInfo, username: JwtUsernameDep, DBSession: DBSessionDep) -> ProjectResponse:
    project_dto = await ts.create_project(
        username,
        payload.name,
        payload.description,
        DBSession,
    )
    return ProjectResponse.from_dto(project_dto)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
) -> list[ProjectResponse]:
    project_dtos = await ts.list_projects(username, DBSession)
    return [ProjectResponse.from_dto(dto) for dto in project_dtos]


@router.delete("/{project_id}", status_code=204)
async def delete_project_by_id(
    project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep, file_service: FileServiceDep
) -> None:
    await ts.delete_project(project_id, username, DBSession, file_service)


@router.get("/{project_id}/info", response_model=ProjectInfo)
async def get_project_info_by_id(project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep) -> ProjectInfo:
    project_info_dto = await ts.get_project_info(project_id, username, DBSession)
    return ProjectInfo(**project_info_dto)


@router.put("/{project_id}/info", response_model=ProjectInfo)
async def update_project_info_by_id(
    project_id: int,
    project_info: ProjectInfo,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
) -> ProjectInfo:
    project_info_dto = await ts.change_project_info(
        project_info.name, project_info.description, project_id, username, DBSession
    )
    return ProjectInfo(**project_info_dto)


@router.post("/{project_id}/invite")
async def invite_another_user_to_the_project_by_username(
    project_id: int, user: str, username: JwtUsernameDep, DBSession: DBSessionDep
) -> None:
    await ts.invite_user(
        invited_username=user,
        project_id=project_id,
        username=username,
        session_factory=DBSession,
    )
