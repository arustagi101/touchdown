from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Highlight(Base):
    __tablename__ = "highlights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    transcript_segment = Column(Text, nullable=True)
    is_included = Column(Boolean, default=True)
    order_index = Column(Integer, nullable=False)
    metadata = Column(JSON, nullable=True)

    video = relationship("Video", backref="highlights")