from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class HighlightClip(BaseModel):
    """Individual highlight clip with timing and description"""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    description: str   # Description of what happens in this clip


class HighlightsMetadata(BaseModel):
    """Metadata for video highlights extraction"""
    video_url: str
    total_duration: float  # Total video duration in seconds
    highlights: List[HighlightClip]
    processing_status: str = "completed"
    success: bool = True
    error: Optional[str] = None


class DownloadResponse(BaseModel):
    """Response from video download API"""
    success: bool
    message: str
    video_url: str
    url_hash: Optional[str] = None
    output_directory: Optional[str] = None
    output_path: Optional[str] = None
    video_info: Optional[Dict[str, Any]] = None
    already_exists: Optional[bool] = None
    error: Optional[str] = None