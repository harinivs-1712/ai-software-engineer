from sqlalchemy import Column, ForeignKey, Integer, String, Text

from sqlalchemy.orm import relationship

from database import Base


class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    role = Column(
        String,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    mode = Column(
        String,
        nullable=True,
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )