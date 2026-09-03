import uuid
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

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

from schemas import ChatRequest, ChatResponse

from services.gemini_service import (
    generate_response_stream,
)

from services.project_service import (
    extract_project,
    read_project_files,
)

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
def chat_stream(request: ChatRequest):

    try:

        project_context = ""

        # --------------------------------
        # Build project context if a
        # project has been selected
        # --------------------------------

        if request.project_id:

            project_content = PROJECT_STORAGE.get(
                request.project_id
            )

            if project_content:

                project_files = read_project_files(
                    project_content
                )

                project_context = build_project_context(
                    project_files,
                    request.message,
                )

        # --------------------------------
        # Send message + project context
        # to Gemini
        # --------------------------------

        return StreamingResponse(
            generate_response_stream(
                request.message,
                request.history,
                request.mode,
                project_context,
            ),
            media_type="text/plain"
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to stream AI response: "
                f"{str(error)}"
            )
        )


@router.post("/upload/project")
async def upload_project(
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

    # --------------------------------
    # Validate ZIP before storing it
    # --------------------------------

    try:

        project_files = extract_project(
            file_content
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP file."
        )

    # --------------------------------
    # Create project ID
    # --------------------------------

    project_id = str(uuid.uuid4())

    # --------------------------------
    # Store project temporarily
    # --------------------------------

    PROJECT_STORAGE[project_id] = file_content

    return {
        "project_id": project_id,
        "filename": file.filename,
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