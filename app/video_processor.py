import asyncio
from typing import List
from .types import HighlightClip


async def extract_highlights_from_video(video_url: str) -> List[HighlightClip]:
    """
    Mock function to extract highlights from video URL.
    In production, this would analyze the video and extract key moments.
    """
    # Simulate processing time
    await asyncio.sleep(3)

    # Mock highlight clips
    mock_highlights = [
        HighlightClip(
            start_time=15.5,
            end_time=45.2,
            description="Introduction and key points overview",
        ),
        HighlightClip(
            start_time=120.0,
            end_time=185.7,
            description="Main demonstration of the product features",
        ),
        HighlightClip(
            start_time=300.3,
            end_time=355.1,
            description="Conclusion and call to action",
        ),
    ]

    return mock_highlights
