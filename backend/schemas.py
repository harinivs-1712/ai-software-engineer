from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    history: list[ChatMessage] = Field(
        default_factory=list
    )
    mode: str = "generate"
    project_id: str | None = None


class ChatResponse(BaseModel):
    reply: str