from fastapi import FastAPI
from .config import settings
from .video_processor import extract_highlights_from_video
from .downloader import download_video
from .clip_extractor import extract_clips
import hashlib
import os

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application built with uv",
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/")
async def processVideo(url: str = "https://www.youtube.com/watch?v=caqxkOKPE2U"):
    try:
        # Create hash of video URL for folder name
        url_hash = hashlib.md5(url.encode()).hexdigest()
        output_dir = f"./output/{url_hash}"

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Download video
        print(f"Downloading video from: {url}")
        video_filename = f"{url_hash}_video.mp4"
        video_path = os.path.join(output_dir, video_filename)
        video_info = await download_video(url, video_path)

        # Step 2: Extract highlights
        print("Extracting highlights...")
        highlights = await extract_highlights_from_video(url)

        # Step 3: Extract clips
        print("Creating highlight clips...")
        clip_files = await extract_clips(highlights, video_path, output_dir)

        return {
            "success": True,
            "video_url": url,
            "output_directory": output_dir,
            "url_hash": url_hash,
            "downloaded_video": video_path,
            "video_info": video_info,
            "highlights_count": len(highlights),
            "clips": clip_files,
            "message": "Video processed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "video_url": url,
            "message": "Failed to process video"
        }


@app.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }
