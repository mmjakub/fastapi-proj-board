from uuid import UUID

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


user_project = Table(
    "user_project",
    Base.metadata,
    Column("user_id", ForeignKey("user.id")),
    Column("project_id", ForeignKey("project.id")),
)


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(16), unique=True)
    password: Mapped[str]

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(secondary=user_project, back_populates="collaborators")


class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    name: Mapped[str]
    description: Mapped[str]

    owner: Mapped[User] = relationship(back_populates="owned_projects")
    collaborators: Mapped[list[User]] = relationship(secondary=user_project, back_populates="projects")
    documents: Mapped[list["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "document"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey(Project.id))
    filename: Mapped[str]

    project: Mapped[Project] = relationship(back_populates="documents")
