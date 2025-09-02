from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


collaborator = Table(
    "collaborator",
    Base.metadata,
    Column("user_id", ForeignKey("user.id")),
    Column("project_id", ForeignKey("project.id")),
)


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    owned_projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        secondary=collaborator, back_populates="collaborators"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}, username='{self.username}', password='{self.password}'>"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, User)
            and self.id == other.id
            and self.username == other.username
            and self.password == other.password
        )


class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    name: Mapped[str]
    description: Mapped[str]

    owner: Mapped[User] = relationship(back_populates="owned_projects")
    collaborators: Mapped[list[User]] = relationship(
        secondary=collaborator, back_populates="projects"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project id={self.id} owner_id={self.owner_id} name='{self.name}' description='{self.description}'>"

    def __eq__(self, other):
        return (
            isinstance(other, Project)
            and other.id == self.id
            and other.owner_id == self.owner_id
            and other.name == self.name
            and other.description == self.description
        )


class Document(Base):
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey(Project.id))
    upload_filename: Mapped[str]

    project: Mapped[Project] = relationship(back_populates="documents")
