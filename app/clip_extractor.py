import asyncio
from typing import List
import ffmpeg
import os

from app.types import HighlightClip


async def extract_clips(
    highlights: List[HighlightClip], video_file: str, output_dir: str
) -> list:
    """Extract highlight clips from video using existing clip_extractor"""
    clip_files = []

    for i, highlight in enumerate(highlights):
        clip_filename = (
            f"highlight_{i + 1}_{highlight.start_time}-{highlight.end_time}.mp4"
        )
        clip_path = os.path.join(output_dir, clip_filename)

        # Use existing extract_clip function
        await extract_clip(
            video_file, highlight.start_time, highlight.end_time, clip_path
        )

        clip_files.append(
            {
                "file": clip_path,
                "start_time": highlight.start_time,
                "end_time": highlight.end_time,
                "description": highlight.description,
            }
        )

    return clip_files


async def extract_clip(
    video_path: str, start_time: float, end_time: float, output_path: str
) -> str:
    try:
        duration = end_time - start_time
        stream = ffmpeg.input(video_path, ss=start_time, t=duration)
        stream = ffmpeg.output(stream, output_path, c="copy")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True)
        )

        return output_path
    except Exception as e:
        raise Exception(f"Failed to extract clip: {str(e)}")
