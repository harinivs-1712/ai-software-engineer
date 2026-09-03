import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "AI Software Engineer"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

CLIENT_ORIGINS = os.getenv(
    "CLIENT_ORIGINS",
    "http://localhost:5173,http://localhost:5174"
).split(",")

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemini-3.6-flash"
)

import os

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-secret-key-change-this",
)