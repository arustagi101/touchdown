from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class VideoBase(BaseModel):
    title: str
    sport_type: Optional[str] = "general"

class VideoCreate(VideoBase):
    original_url: Optional[str] = None

class VideoResponse(VideoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    video_type: str
    duration: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    processing_progress: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class VideoStatus(BaseModel):
    status: str
    progress: int
    error_message: Optional[str] = None