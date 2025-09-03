from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.sql_alchemy import orm
from app.core.errors import ResourceNotFound
from app.core.ports.repository import DataRepository
from app.core.models import Project, Document, Username, User


class SADataRepository(DataRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: Username, password: str) -> User:
        orm_user = orm.User(username=username, password=password)
        self.session.add(orm_user)
        await self.session.flush()
        return User(
            id=orm_user.id, username=orm_user.username, password=orm_user.password
        )

    async def user_exists(self, username: Username) -> bool:
        orm_user = await self.session.scalar(
            select(orm.User).where(orm.User.username == username)
        )
        return orm_user is not None

    def _document_to_orm(self, document: Document) -> orm.Document:
        return orm.Document(
            id=document.id,
            project_id=document.project_id,
            upload_filename=document.upload_filename,
        )

    def _document_from_orm(self, orm_document: orm.Document) -> Document:
        return Document(
            id=orm_document.id,
            project_id=orm_document.project.id,
            upload_filename=orm_document.upload_filename,
        )

    def _project_from_orm(self, orm_project: orm.Project) -> Project:
        project = Project(
            id=orm_project.id,
            name=orm_project.name,
            description=orm_project.description,
            owner=orm_project.owner.username,
            collaborators={u.username for u in orm_project.collaborators},
            documents=list(map(self._document_from_orm, orm_project.documents)),
        )
        return project

    async def get_project_by_id(self, project_id: int) -> Project:
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
        return self._project_from_orm(orm_project)

    async def get_all_projects_by_username(self, user: Username) -> list[Project]:
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
        return list(map(self._project_from_orm, orm_projects))

    async def create_project(
        self, owner: Username, project_name: str, project_description: str
    ) -> Project:
        orm_owner = await self._get_orm_user(owner)
        orm_project = orm.Project(name=project_name, description=project_description)
        orm_project.owner = orm_owner
        orm_project.collaborators = [orm_owner]
        orm_project.documents = []
        self.session.add(orm_project)
        await self.session.flush()
        return self._project_from_orm(orm_project)

    async def save_project(self, project: Project) -> Project:
        orm_collaborators = {
            u.username: u
            for u in await self.session.scalars(
                select(orm.User).where(orm.User.username.in_(project.collaborators))
            )
        }

        orm_owner = orm_collaborators.get(project.owner) or (
            await self.session.scalars(
                select(orm.User).where(orm.User.username == project.owner)
            ).one()
        )

        if project.id:
            orm_project = (
                await self.session.scalars(
                    select(orm.Project)
                    .where(orm.Project.id == project.id)
                    .options(
                        selectinload(orm.Project.collaborators),
                        selectinload(orm.Project.documents),
                    )
                )
            ).one()
            orm_project.name = project.name
            orm_project.description = project.description
            orm_project.owner = orm_owner
        else:
            orm_project = orm.Project(
                owner_id=orm_owner.id,
                name=project.name,
                description=project.description,
            )
            self.session.add(orm_project)

        orm_project.collaborators = list(orm_collaborators.values())
        orm_project.documents = [self._document_to_orm(d) for d in project.documents]

        await self.session.flush()
        return self._project_from_orm(orm_project)

    async def delete_project(self, project: Project):
        orm_project = await self.session.scalar(
            select(orm.Project).where(orm.Project.id == project.id)
        )
        await self.session.delete(orm_project)
        await self.session.flush()

    async def create_document(self, project_id: int, upload_filename) -> Document:
        orm_document = orm.Document(
            project_id=project_id, upload_filename=upload_filename
        )
        self.session.add(orm_document)
        await self.session.flush()
        await orm_document.awaitable_attrs.project
        return self._document_from_orm(orm_document)

    async def get_project_by_document_id(self, document_id: int) -> Project:
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
        return self._project_from_orm(orm_project)

    async def _get_orm_user(self, username: Username) -> orm.User:
        orm_user = await self.session.scalar(
            select(orm.User).where(orm.User.username == username)
        )
        if orm_user is None:
            raise ResourceNotFound(f"User with username={username} not found")
        return orm_user

    async def get_user(self, username: Username) -> User:
        orm_user = await self._get_orm_user(username)
        return User(
            id=orm_user.id, username=orm_user.username, password=orm_user.password
        )
