import hashlib
import asyncio
from typing import List
from fastapi import FastAPI

from app.clip_extractor import extract_clips

from .config import settings
from .video_processor import extract_highlights_from_video
from .downloader import download_video
from .types import DownloadResponse, HighlightClip

import os

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application built with uv",
    version=settings.app_version,
    debug=settings.debug,
)

@app.get("/download", response_model=DownloadResponse)
async def download(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U") -> DownloadResponse:
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
                already_exists=True
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
            already_exists=False
        )

    except Exception as e:
        return DownloadResponse(
            success=False,
            error=str(e),
            message="Failed to download video",
            video_url=url
        )

@app.get("/highlights", response_model=List[HighlightClip])
async def highlights(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U") -> List[HighlightClip]:
    return await extract_highlights_from_video(url)

@app.get("/")
async def processVideo(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"):
    try:
        # Step 1 & 2: Run download and highlight extraction in parallel
        print(f"Starting parallel processing for: {url}")
        download_task = download(url)
        highlights_task = extract_highlights_from_video(url)

        # Wait for both tasks to complete
        download_result, highlights = await asyncio.gather(download_task, highlights_task)

        if not download_result.success:
            return download_result  # Return download error if failed

        # Step 3: Extract clips
        # print("Creating highlight clips...")
        # clip_files = await extract_clips(highlights, download_result.output_path, download_result.output_directory)

        return {
            "success": True,
            "video_url": url,
            "download_step": download_result,
            "highlights_count": len(highlights),
            "message": "Video processed successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "video_url": url,
            "message": "Failed to process video",
        }


@app.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }
