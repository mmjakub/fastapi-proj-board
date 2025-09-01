from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import orm
from ..core.errors import ResourceNotFound
from ..core.ports.repository import ProjectRepository
from ..core.models import Project, Document, Username


class SAProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _document_orm_to_domain(self, orm_document: orm.Document) -> Document:
        return Document(
            id=orm_document.id,
            project_id=orm_document.project.id,
            upload_filename=orm_document.upload_filename,
        )

    def _project_orm_to_domain(self, orm_project: orm.Project) -> Project:
        project = Project(
            id=orm_project.id,
            name=orm_project.name,
            description=orm_project.description,
            owner=orm_project.owner.username,
            collaborators={u.username for u in orm_project.collaborators},
            documents=list(map(self._document_orm_to_domain, orm_project.documents)),
        )
        return project

    async def get(self, project_id: int) -> Project:
        orm_project = await self.session.scalar(
            select(orm.Project)
            .where(orm.Project.id == project_id)
            .options(
                selectinload(orm.Project.owner),
                selectinload(orm.Project.collaborators),
                selectinload(orm.Project.documents),
            )
        )
        if orm_project is None:
            raise ResourceNotFound(f"Project with id={project_id} not found")
        return self._project_orm_to_domain(orm_project)

    async def get_all(self, user: Username) -> list[Project]:
        orm_projects = (
            await self.session.scalars(
                select(orm.Project)
                .join(orm.Project.collaborators)
                .where(orm.User.username == user)
                .options(
                    selectinload(orm.Project.owner),
                    selectinload(orm.Project.collaborators),
                    selectinload(orm.Project.documents),
                )
            )
        ).all()
        return list(map(self._project_orm_to_domain, orm_projects))

    async def create(
        self, owner: Username, project_name: str, project_description: str
    ) -> Project:
        orm_owner = await self._get_user_by_username(owner)
        orm_project = orm.Project(name=project_name, description=project_description)
        orm_project.owner = orm_owner
        orm_project.collaborators = [orm_owner]
        orm_project.documents = []
        self.session.add(orm_project)
        await self.session.flush()
        return self._project_orm_to_domain(orm_project)

    async def save(self, project: Project) -> Project:
        orm_project = orm.Project(
            id=project.id, name=project.name, description=project.description
        )
        orm_project.owner = await self._get_user_by_username(project.owner)
        orm_project.collaborators = [
            await self._get_user_by_username(un) for un in project.collaborators
        ]
        orm_project.documents = [self._document_to_orm(d) for d in project.documents]
        orm_project = await self.session.merge(orm_project)
        await self.session.flush()
        return self._project_orm_to_domain(orm_project)

    async def delete(self, project: Project):
        raise NotImplementedError

    async def create_document(self, project_id: int, upload_filename) -> Document:
        orm_document = orm.Document(
            project_id=project_id, upload_filename=upload_filename
        )
        self.session.add(orm_document)
        await self.session.flush()
        await orm_document.awaitable_attrs.project
        return self._document_orm_to_domain(orm_document)

    async def get_by_document_id(self, document_id: int) -> Project:
        orm_project = await self.session.scalar(
            select(orm.Project)
            .join(orm.Project.documents)
            .where(orm.Document.id == document_id)
            .options(
                selectinload(orm.Project.owner),
                selectinload(orm.Project.collaborators),
                selectinload(orm.Project.documents),
            )
        )
        if orm_project is None:
            raise ResourceNotFound(f"Document with id={document_id} not found.")
        return self._project_orm_to_domain(orm_project)

    def _document_to_orm(self, document: Document) -> orm.Document:
        return orm.Document(
            id=document.id,
            project_id=document.project_id,
            upload_filename=document.upload_filename,
        )

    async def _get_user_by_username(self, username: Username) -> orm.User:
        user = await self.session.scalar(
            select(orm.User).where(orm.User.username == username)
        )
        if user is None:
            raise ResourceNotFound(f"User with username={username} not found")
        return user
