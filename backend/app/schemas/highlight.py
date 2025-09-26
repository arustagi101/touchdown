from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
import uuid

class HighlightBase(BaseModel):
    start_time: float
    end_time: float
    score: float
    category: Optional[str] = None
    description: Optional[str] = None

class HighlightCreate(HighlightBase):
    video_id: uuid.UUID
    transcript_segment: Optional[str] = None

class HighlightUpdate(BaseModel):
    is_included: Optional[bool] = None
    description: Optional[str] = None
    order_index: Optional[int] = None

class HighlightResponse(HighlightBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    duration: float
    is_included: bool
    order_index: int
    metadata: Optional[Dict[str, Any]] = None