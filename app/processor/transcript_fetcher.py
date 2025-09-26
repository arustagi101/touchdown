import re
from typing import List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable


class TranscriptEntry:
    """Represents a single transcript entry with timing information."""
    
    def __init__(self, text: str, start: float, duration: float):
        self.text = text.strip()
        self.start = start
        self.duration = duration
        self.end = start + duration


class YouTubeTranscriptFetcher:
    """Fetches and processes YouTube video transcripts."""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def fetch_transcript(video_url: str) -> List[TranscriptEntry]:
        """
        Fetch transcript for a YouTube video.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            List of TranscriptEntry objects
            
        Raises:
            ValueError: If video ID cannot be extracted or transcript not available
        """
        video_id = YouTubeTranscriptFetcher.extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
        
        try:
            # Get transcript data using the instance method
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id, languages=['en'])
            transcript_data = fetched_transcript.to_raw_data()
            
            return [
                TranscriptEntry(
                    text=entry['text'],
                    start=entry['start'],
                    duration=entry['duration']
                )
                for entry in transcript_data
            ]
            
        except TranscriptsDisabled:
            raise ValueError("Transcripts are disabled for this video")
        except NoTranscriptFound:
            raise ValueError("No transcript found for this video")
        except VideoUnavailable:
            raise ValueError("Video is unavailable or private")
        except Exception as e:
            raise ValueError(f"Error fetching transcript: {str(e)}")
    
    @staticmethod
    def format_transcript_for_analysis(transcript: List[TranscriptEntry]) -> str:
        """
        Format transcript entries for OpenAI analysis.
        
        Args:
            transcript: List of TranscriptEntry objects
            
        Returns:
            Formatted string with timestamps and text
        """
        formatted_lines = []
        
        for entry in transcript:
            # Format timestamp as [MM:SS] or [HH:MM:SS]
            start_time = entry.start
            hours = int(start_time // 3600)
            minutes = int((start_time % 3600) // 60)
            seconds = int(start_time % 60)
            
            if hours > 0:
                timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
            else:
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            formatted_lines.append(f"{timestamp} {entry.text}")
        
        return "\n".join(formatted_lines)
    
    @staticmethod
    def get_total_duration(transcript: List[TranscriptEntry]) -> float:
        """Get total duration of the video from transcript."""
        if not transcript:
            return 0.0
        
        last_entry = transcript[-1]
        return last_entry.end