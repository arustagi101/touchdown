from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Touchdown"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/touchdown")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "touchdown-videos")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    MAX_VIDEO_SIZE_MB: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
    MAX_PROCESSING_TIME_MINUTES: int = int(os.getenv("MAX_PROCESSING_TIME_MINUTES", "30"))

    TEMP_DIR: str = "/tmp/touchdown"
    HIGHLIGHTS_MIN_DURATION: int = 5
    HIGHLIGHTS_MAX_DURATION: int = 30
    DEFAULT_HIGHLIGHT_COUNT: int = 10

    WHISPER_MODEL: str = "whisper-1"
    GPT_MODEL: str = "gpt-4-turbo-preview"

    class Config:
        case_sensitive = True

settings = Settings()