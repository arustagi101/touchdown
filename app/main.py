import hashlib
from fastapi import FastAPI

from .config import settings
from .video_processor import extract_highlights_from_video
from .downloader import download_video
from .clip_extractor import extract_clips

import os

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application built with uv",
    version=settings.app_version,
    debug=settings.debug,
)

@app.get("/download")
async def download(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"):
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
            return {
                "success": True,
                "message": "Video already downloaded",
                "video_url": url,
                "url_hash": url_hash,
                "output_directory": output_dir,
                "output_path": output_path,
                "already_exists": True
            }

        # Download video
        print(f"Downloading video from: {url}")
        video_info = await download_video(url, output_path)

        return {
            "success": True,
            "message": "Video downloaded successfully",
            "video_url": url,
            "url_hash": url_hash,
            "output_directory": output_dir,
            "output_path": output_path,
            "video_info": video_info,
            "already_exists": False
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to download video",
            "video_url": url
        }


@app.get("/")
async def processVideo(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"):
    try:
        
        video_info = await download(url)

        # Step 2: Extract highlights
        print("Extracting highlights...")
        highlights = await extract_highlights_from_video(url)

        # Step 3: Extract clips
        print("Creating highlight clips...")
        # clip_files = await extract_clips(highlights, video_path, output_dir)

        return {
            "success": True,
            "video_url": url,
            # "output_directory": output_dir,
            # "url_hash": url_hash,
            # "downloaded_video": video_path,
            "video_info": video_info,
            "highlights_count": len(highlights),
            # "clips": clip_files,
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
