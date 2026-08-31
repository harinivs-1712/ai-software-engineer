from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas import ChatRequest, ChatResponse

from services.gemini_service import (
    generate_response_stream,
)


router = APIRouter()


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

        return StreamingResponse(
            generate_response_stream(
                request.message,
                request.history,
                request.mode
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