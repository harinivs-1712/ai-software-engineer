from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    conversation_id: str | int | None = None
    message: str
    mode: str = "generate"
    project_id: str | int | None = None


class ChatResponse(BaseModel):
    reply: str
    
    
class ConversationCreate(BaseModel):

    title: str = "New Chat"


class ConversationRename(BaseModel):

    title: str
    
class MessageCreate(BaseModel):

    role: str
    content: str
    mode: str | None = None
    
class ProjectResponse(BaseModel):

    id: int
    name: str
    file_count: int


class ProjectFileResponse(BaseModel):

    id: int
    path: str
    content: str