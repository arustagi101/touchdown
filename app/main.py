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


@app.get("/download", response_model=DownloadResponse)
async def download(
    url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U",
) -> DownloadResponse:
    try:
        # Create hash of video URL for folder name
        url_hash = hashlib.md5(url.encode()).hexdigest()
        output_dir = f"./output/{url_hash}"
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
    url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U", max_highlights: int = 5
) -> List[HighlightClip]:
    extractor = HighlightExtractor()
    print(f"Analyzing video: {url}")

    # Get the JSON result from the extractor
    result = extractor.extract_highlights_to_json(url, max_highlights)

    # Map JSON result to HighlightClip objects
    highlight_clips = []
    for highlight_data in result:
        clip = HighlightClip(
            start_time=highlight_data["start_time"],
            end_time=highlight_data["end_time"],
            start_time_formatted=highlight_data.get("start_time_formatted"),
            end_time_formatted=highlight_data.get("end_time_formatted"),
            duration=highlight_data.get("duration"),
            description=highlight_data["description"],
            importance_score=highlight_data.get("importance_score"),
            category=highlight_data.get("category"),
        )
        highlight_clips.append(clip)

    return highlight_clips


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
