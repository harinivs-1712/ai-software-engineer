from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.conversation import Conversation
from models.project import Project


def get_user_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
):

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


def get_user_project(
    db: Session,
    project_id: int,
    user_id: int,
):

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        .first()
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return project