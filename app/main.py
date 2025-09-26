import hashlib
import asyncio
from typing import List
from fastapi import FastAPI

from .processor.highlight_extractor import HighlightExtractor

from .config import settings
from .downloader import download_video
from .clip_extractor import extract_clips
from .types import DownloadResponse, HighlightClip

import os

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application built with uv",
    version=settings.app_version,
    debug=settings.debug,
)

def hash_url(url: str):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    output_dir = f"./output/{url_hash}"
    return url_hash, output_dir

@app.get("/download", response_model=DownloadResponse)
async def download(
    url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U",
) -> DownloadResponse:
    try:
        # Create hash of video URL for folder name
        url_hash, output_dir = hash_url(url)
        output_path = os.path.join(output_dir, "video.mp4")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Check if video already exists
        if os.path.exists(output_path):
            print(f"Video already exists at: {output_path}")
            return DownloadResponse(
                success=True,
                message="Video already downloaded",
                video_url=url,
                url_hash=url_hash,
                output_directory=output_dir,
                output_path=output_path,
                already_exists=True,
            )

        # Download video
        print(f"Downloading video from: {url}")
        video_info = await download_video(url, output_path)

        return DownloadResponse(
            success=True,
            message="Video downloaded successfully",
            video_url=url,
            url_hash=url_hash,
            output_directory=output_dir,
            output_path=output_path,
            video_info=video_info,
            already_exists=False,
        )

    except Exception as e:
        return DownloadResponse(
            success=False,
            error=str(e),
            message="Failed to download video",
            video_url=url,
        )


@app.get("/highlights", response_model=List[HighlightClip])
async def highlights(
    url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U",
    max_highlights: int = 5,
    overwrite: bool = False
) -> List[HighlightClip]:
    try:
        url_hash, output_dir = hash_url(url)
        clips_json_path = os.path.join(output_dir, "clips.json")

        # Check if clips.json exists and overwrite is False
        if os.path.exists(clips_json_path) and not overwrite:
            print(f"Loading cached highlights from: {clips_json_path}")
            import json
            with open(clips_json_path, 'r') as f:
                cached_result = json.load(f)

            # Convert cached result to HighlightClip objects
            highlight_clips = []
            for highlight_data in cached_result:
                clip = HighlightClip(**highlight_data)
                highlight_clips.append(clip)

            print(f"Loaded {len(highlight_clips)} cached highlights")
            return highlight_clips

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        extractor = HighlightExtractor()
        print(f"Analyzing video: {url} (max_highlights: {max_highlights})")

        # Get the JSON result from the extractor
        result = extractor.extract_highlights_to_json(url, max_highlights)

        # Debug: Print the result structure
        print(f"Result type: {type(result)}")
        print(f"Result content: {result}")

        # Handle different possible result structures
        if isinstance(result, dict):
            # If result is a dict, it might contain a list of highlights
            if 'highlights' in result:
                highlights_data = result['highlights']
            else:
                # Treat the dict as a single highlight
                highlights_data = [result]
        elif isinstance(result, list):
            # Result is already a list of highlights
            highlights_data = result
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")

        # Map JSON result to HighlightClip objects
        highlight_clips = []
        for highlight_data in highlights_data:
            # Ensure highlight_data is a dictionary
            if not isinstance(highlight_data, dict):
                print(f"Skipping invalid highlight data: {highlight_data}")
                continue

            clip = HighlightClip(
                start_time=highlight_data.get("start_time", 0.0),
                end_time=highlight_data.get("end_time", 0.0),
                start_time_formatted=highlight_data.get("start_time_formatted"),
                end_time_formatted=highlight_data.get("end_time_formatted"),
                duration=highlight_data.get("duration"),
                description=highlight_data.get("description", "No description available"),
                importance_score=highlight_data.get("importance_score"),
                category=highlight_data.get("category"),
            )
            highlight_clips.append(clip)

        # Save highlights to clips.json for caching
        import json
        clips_data = [clip.dict() for clip in highlight_clips]
        with open(clips_json_path, 'w') as f:
            json.dump(clips_data, f, indent=2)

        print(f"Saved {len(highlight_clips)} highlights to: {clips_json_path}")
        return highlight_clips

    except Exception as e:
        print(f"Error in highlights endpoint: {str(e)}")
        # Return empty list or raise HTTPException
        return []


@app.get("/")
async def processVideo(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"):
    try:
        # Step 1 & 2: Run download and highlight extraction in parallel
        print(f"Starting parallel processing for: {url}")
        download_task = download(url)
        highlights_task = highlights(url)

        # Wait for both tasks to complete
        download_result, highlights_result = await asyncio.gather(
            download_task, highlights_task
        )

        if not download_result.success:
            return download_result  # Return download error if failed

        # Step 3: Extract clips
        # print("Creating highlight clips...")
        clip_files = await extract_clips(
            highlights_result,
            download_result.output_path,
            download_result.output_directory,
        )

        return {
            "success": True,
            "video_url": url,
            "download_step": download_result,
            "highlights_count": len(highlights_result),
            "clips": clip_files,
            "message": "Video processed successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "video_url": url,
            "message": "Failed to process video",
        }


# @app.get("/extract-clips")
# async def extract_clips_from_video(
#     url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"
# ):
#     """
#     Extract highlight clips from a video URL.

#     Args:
#         url: YouTube video URL (defaults to a sample video)
#     """
#     try:
#         # Create hash of video URL for folder name (same as download)
#         url_hash = hashlib.md5(url.encode()).hexdigest()
#         output_dir = f"./output/{url_hash}"
#         video_path = os.path.join(output_dir, "video.mp4")

#         # Check if video file exists locally
#         if not os.path.exists(video_path):
#             return {
#                 "success": False,
#                 "error": f"Video file not found locally: {video_path}",
#                 "message": "Please download the video first using /download endpoint",
#                 "video_url": url,
#                 "url_hash": url_hash,
#                 "suggested_action": f"Run: GET /download?url={url}"
#             }

#         # Create clips subdirectory within the same output folder
#         clips_dir = os.path.join(output_dir, "clips")
#         os.makedirs(clips_dir, exist_ok=True)

#         # Extract highlights from the video
#         print(f"Extracting highlights from: {url}")
#         highlights = await extract_highlights_from_video(url)

#         # Extract clips using the highlights
#         clip_files = await extract_clips(highlights, video_path, clips_dir)

#         # Calculate total size
#         total_size = sum(os.path.getsize(clip["file"]) for clip in clip_files)

#         return {
#             "success": True,
#             "message": f"Clips extracted successfully to {clips_dir}",
#             "video_url": url,
#             "url_hash": url_hash,
#             "video_path": video_path,
#             "clips_directory": clips_dir,
#             "highlights_count": len(highlights),
#             "clips": clip_files,
#             "total_size_bytes": total_size,
#             "total_size_mb": round(total_size / 1024 / 1024, 2)
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "message": "Failed to extract clips",
#             "video_url": url
#         }


@app.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }
