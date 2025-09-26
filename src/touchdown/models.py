from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Highlight:
    """Represents a single highlight moment from a sports video."""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    description: str   # Description of the highlight
    importance_score: float  # Score from 0-10 indicating importance
    category: str      # Type of highlight (goal, save, foul, etc.)
    
    @property
    def duration(self) -> float:
        """Duration of the highlight in seconds."""
        return self.end_time - self.start_time
    
    @property
    def start_time_formatted(self) -> str:
        """Format start time as MM:SS or HH:MM:SS."""
        return self._format_time(self.start_time)
    
    @property
    def end_time_formatted(self) -> str:
        """Format end time as MM:SS or HH:MM:SS."""
        return self._format_time(self.end_time)
    
    def _format_time(self, seconds: float) -> str:
        """Convert seconds to formatted time string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


@dataclass
class VideoAnalysis:
    """Contains the complete analysis of a sports video."""
    video_url: str
    video_title: Optional[str]
    total_duration: float  # Total video duration in seconds
    highlights: List[Highlight]
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "video_url": self.video_url,
            "video_title": self.video_title,
            "total_duration": self.total_duration,
            "total_duration_formatted": self._format_time(self.total_duration),
            "highlights": [
                {
                    "start_time": h.start_time,
                    "end_time": h.end_time,
                    "start_time_formatted": h.start_time_formatted,
                    "end_time_formatted": h.end_time_formatted,
                    "duration": h.duration,
                    "description": h.description,
                    "importance_score": h.importance_score,
                    "category": h.category
                }
                for h in self.highlights
            ]
        }
    
    def _format_time(self, seconds: float) -> str:
        """Convert seconds to formatted time string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
