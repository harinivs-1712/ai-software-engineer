from datetime import datetime
import uuid
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, Conversation, Message, Project, ProjectFile
from services.ownership_service import (
    get_user_conversation,
    get_user_project,
)
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)
from auth import get_current_user
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from pathlib import Path

from schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationRename,
    MessageCreate,
)

from services.gemini_service import (
    generate_response_stream,
    generate_response_with_tools,
)

from services.project_service import (
    extract_project,
    read_project_files,
    MAX_PROJECT_SIZE,
)

from services.project_storage_service import create_project

from services.project_analyzer import (
    analyze_project,
)

from services.context_builder import (
    build_project_context,
)

from services.file_service import (
    get_file_extension,
    is_supported_file,
    validate_file_size,
    read_text_file,
)


router = APIRouter()


# Temporary project storage
# This will be replaced by database/storage
# in a later phase.
PROJECT_STORAGE = {}


def get_conversation_history(
    db: Session,
    conversation_id: int,
):

    return (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.id.asc())
        .all()
    )


class RegisterRequest(BaseModel):

    email: str
    password: str


class LoginRequest(BaseModel):

    email: str
    password: str


@router.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "AI Software Engineer API"
    }


@router.get("/api/info")
def api_info():

    return {
        "name": "AI Software Engineer",
        "version": "1.0.0",
        "status": "development"
    }


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if data.conversation_id is None:
        raise HTTPException(
            status_code=400,
            detail="conversation_id is required.",
        )

    try:
        conversation_id = int(data.conversation_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="conversation_id must be an integer.",
        )

    conversation = get_user_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    previous_messages = get_conversation_history(
        db,
        conversation.id,
    )

    user_message = Message(
        role="user",
        content=data.message,
        mode=data.mode,
        conversation_id=conversation.id,
    )

    db.add(user_message)
    conversation.updated_at = datetime.utcnow()
    db.commit()

    project_context = ""

    # --------------------------------
    # Build project context from database or memory
    # --------------------------------

    if data.project_id:
        try:
            p_id = int(data.project_id)
            project = get_user_project(
                db,
                p_id,
                current_user.id,
            )

            db_files = (
                db.query(ProjectFile)
                .filter(ProjectFile.project_id == project.id)
                .all()
            )

            if db_files:
                project_files = [
                    {"path": f.path, "content": f.content}
                    for f in db_files
                ]
                project_context = build_project_context(
                    project_files,
                    data.message,
                )
        except (ValueError, TypeError):
            pass

        if not project_context:
            project_content = PROJECT_STORAGE.get(
                str(data.project_id)
            ) or PROJECT_STORAGE.get(data.project_id)

            if project_content:
                project_files = read_project_files(
                    project_content
                )
                project_context = build_project_context(
                    project_files,
                    data.message,
                )

    active_proj_id = None
    if data.project_id:
        try:
            active_proj_id = int(data.project_id)
        except (ValueError, TypeError):
            pass

    def response_stream():
        assistant_response = ""

        for chunk in generate_response_stream(
            data.message,
            previous_messages,
            data.mode,
            project_context,
            user_id=current_user.id,
            project_id=active_proj_id,
            db=db,
        ):
            assistant_response += chunk
            yield chunk

        if assistant_response.strip():
            assistant_message = Message(
                role="assistant",
                content=assistant_response,
                mode=data.mode,
                conversation_id=conversation.id,
            )
            db.add(assistant_message)
            conversation.updated_at = datetime.utcnow()
            db.commit()

    return StreamingResponse(
        response_stream(),
        media_type="text/plain"
    )


@router.post("/projects/upload")
async def upload_project(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    if not file.filename.lower().endswith(".zip"):

        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are supported.",
        )

    file_content = await file.read()

    if len(file_content) > MAX_PROJECT_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Project ZIP exceeds the 20 MB limit.",
        )

    try:

        project_files = read_project_files(
            file_content
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP file.",
        )

    if not project_files:

        raise HTTPException(
            status_code=400,
            detail="No supported source files found.",
        )

    project_name = Path(
        file.filename
    ).stem

    project = create_project(
        db=db,
        user_id=current_user.id,
        project_name=project_name,
        files=project_files,
    )

    return {
        "id": project.id,
        "name": project.name,
        "file_count": len(project_files),
    }


@router.post("/analyze/project")
async def analyze_uploaded_project(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )

    if not file.filename.lower().endswith(
        ".zip"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are supported."
        )

    file_content = await file.read()

    if len(file_content) > MAX_PROJECT_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Project ZIP exceeds the 20 MB limit.",
        )

    try:

        analysis = analyze_project(
            file_content
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Project analysis failed: {error}"
            )
        )

    return {
        "filename": file.filename,
        "file_count": len(analysis),
        "analysis": analysis,
    }
    
    
    
@router.post("/auth/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    try:
        existing_user = db.query(User).filter(
            User.email == data.email
        ).first()

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail="Email is already registered.",
            )

        password_hash = hash_password(
            data.password
        )

        user = User(
            email=data.email,
            password_hash=password_hash,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "message": "User registered successfully.",
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )
    
    
@router.post("/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        user.id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }
    
@router.get("/auth/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return {
        "id": current_user.id,
        "email": current_user.email,
    }
    
    
@router.post("/conversations")
def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    conversation = Conversation(
        title=data.title,
        user_id=current_user.id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }
    
    
@router.get("/conversations")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id
        )
        .order_by(
            Conversation.updated_at.desc()
        )
        .all()
    )

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
        for conversation in conversations
    ]
    
@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    conversation = get_user_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id
        )
        .order_by(Message.id.asc())
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "mode": message.mode,
            }
            for message in messages
        ],
    }
    
@router.post(
    "/conversations/{conversation_id}/messages"
)
def add_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    conversation = get_user_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    message = Message(
        role=data.role,
        content=data.content,
        mode=data.mode,
        conversation_id=conversation.id,
    )

    db.add(message)

    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "mode": message.mode,
    }
    
@router.patch("/conversations/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    data: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    conversation = get_user_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    conversation.title = data.title
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "updated_at": conversation.updated_at,
    }
    
@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    conversation = get_user_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully."
    }
    
    
@router.get("/projects")
def get_projects(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .all()
    )

    return [
        {
            "id": project.id,
            "name": project.name,
            "file_count": len(project.files),
            "created_at": project.created_at,
        }
        for project in projects
    ]
    
@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    project = get_user_project(
        db,
        project_id,
        current_user.id,
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return {
        "id": project.id,
        "name": project.name,
        "file_count": len(project.files),
        "files": [
            {
                "id": file.id,
                "path": file.path,
                "content": file.content,
            }
            for file in project.files
        ],
    }
    
@router.get(
    "/projects/{project_id}/files/{file_id}"
)
def get_project_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    project = get_user_project(
        db,
        project_id,
        current_user.id,
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    project_file = (
        db.query(ProjectFile)
        .filter(
            ProjectFile.id == file_id,
            ProjectFile.project_id == project.id,
        )
        .first()
    )

    if project_file is None:

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return {
        "id": project_file.id,
        "path": project_file.path,
        "content": project_file.content,
    }
    
    
@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    project = get_user_project(
        db,
        project_id,
        current_user.id,
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully."
    }