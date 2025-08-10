import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .document import DocumentResponse
from ..models import User, Project
from ..dependencies import DBSessionDep, FileServiceDep
from ..jwt import JwtUsernameDep

router = APIRouter(prefix="/projects", tags=["project"])


class ProjectInfo(BaseModel):
    name: str
    description: str

    @classmethod
    def from_sa_orm(cls, project: Project) -> "ProjectInfo":
        return cls(name=project.name, description=project.description)


class ProjectResponse(BaseModel):
    id: int
    info: ProjectInfo
    documents: list[DocumentResponse]
    owner: str

    @classmethod
    def from_sa_orm(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            info=ProjectInfo.from_sa_orm(project),
            owner=project.owner.username,
            documents=[DocumentResponse.from_sa_orm(d) for d in project.documents],
        )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectInfo, username: JwtUsernameDep, DBSession: DBSessionDep) -> ProjectResponse:
    async with DBSession() as session, session.begin():
        user = await session.scalar(select(User).where(User.username == username))
        project = Project(
            owner=user,
            name=payload.name,
            description=payload.description,
            collaborators=[user],
            documents=[],
        )
        session.add(project)
        await session.flush()
        return ProjectResponse.from_sa_orm(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
) -> list[ProjectResponse]:
    results: list[ProjectResponse] = []
    async with DBSession() as session, session.begin():
        user = (
            (
                await session.scalars(
                    select(User)
                    .where(User.username == username)
                    .options(
                        joinedload(User.projects).options(joinedload(Project.owner), joinedload(Project.documents))
                    )
                )
            )
            .unique()
            .one()
        )
        results = [ProjectResponse.from_sa_orm(p) for p in user.projects]
    return results


@router.delete("/{project_id}", status_code=204)
async def delete_project_by_id(
    project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep, file_service: FileServiceDep
) -> None:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        project = await session.scalar(select(Project).where(Project.id == project_id))

        if project is None:
            raise HTTPException(status_code=404)

        await project.awaitable_attrs.owner
        if user is not project.owner:
            raise HTTPException(status_code=403)

        await project.awaitable_attrs.documents

        await asyncio.gather(*(file_service.delete(doc.id) for doc in project.documents), session.delete(project))


@router.get("/{project_id}/info", response_model=ProjectInfo)
async def get_project_info_by_id(project_id: int, username: JwtUsernameDep, DBSession: DBSessionDep) -> ProjectInfo:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if project is None:
            raise HTTPException(status_code=404)
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)
        return ProjectInfo.from_sa_orm(project)


@router.put("/{project_id}/info", response_model=ProjectInfo)
async def update_project_info_by_id(
    project_id: int,
    project_info: ProjectInfo,
    username: JwtUsernameDep,
    DBSession: DBSessionDep,
) -> ProjectInfo:
    async with DBSession() as session, session.begin():
        user = (await session.scalars(select(User).where(User.username == username))).one()
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if project is None:
            raise HTTPException(status_code=404)
        await project.awaitable_attrs.collaborators
        if user not in project.collaborators:
            raise HTTPException(status_code=403)
        project.name = project_info.name
        project.description = project_info.description
        await session.merge(project)
        return ProjectInfo.from_sa_orm(project)


@router.post("/{project_id}/invite")
async def invite_another_user_to_the_project_by_username(
    project_id: int, user: str, username: JwtUsernameDep, DBSession: DBSessionDep
) -> None:
    async with DBSession() as session, session.begin():
        inviting_user = (await session.scalars(select(User).where(User.username == username))).one()
        invited_user = await session.scalar(select(User).where(User.username == user))
        if invited_user is None:
            raise HTTPException(status_code=400, detail=f"User <{user}> does not exist.")
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if project is None:
            raise HTTPException(status_code=404)
        await project.awaitable_attrs.owner
        if inviting_user is not project.owner:
            raise HTTPException(status_code=403, detail="You must be project owner to invite others")
        await project.awaitable_attrs.collaborators
        if invited_user in project.collaborators:
            raise HTTPException(status_code=400, detail=f"User <{user}> already works on this project.")
        project.collaborators.append(invited_user)
        await session.merge(project)
