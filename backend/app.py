from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router


from config import CLIENT_ORIGINS

app = FastAPI(
    title="AI Software Engineer API",
    description="Backend API for the AI Software Engineer",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CLIENT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "AI Software Engineer API is running"
    }