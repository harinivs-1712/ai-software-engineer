from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Project(Base):

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    files = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectFile(Base):

    __tablename__ = "project_files"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    path = Column(
        String,
        nullable=False,
    )

    content = Column(
        String,
        nullable=False,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="files",
    )