from sqlalchemy.orm import Session

from models.conversation import Conversation
from models.message import Message


def get_conversation_history(
    db: Session,
    conversation_id: int,
):

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(
            Message.id.asc()
        )
        .all()
    )

    return messages


def build_gemini_history(messages):

    history = []

    for message in messages:

        history.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return history