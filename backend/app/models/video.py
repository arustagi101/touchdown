from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoType(str, enum.Enum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"
    URL = "url"

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    original_url = Column(Text, nullable=True)
    local_path = Column(Text, nullable=True)
    s3_path = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    sport_type = Column(String(50), nullable=True)
    video_type = Column(Enum(VideoType), nullable=False)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    processing_progress = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)