import asyncio
from typing import Dict
import yt_dlp


async def download_video(url: str, output_path: str) -> Dict:
    ydl_opts = {
        "outtmpl": output_path,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    loop = asyncio.get_event_loop()

    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {
                "title": info.get("title", "Untitled"),
                "duration": info.get("duration", 0),
                "fps": info.get("fps", 30),
                "width": info.get("width", 1920),
                "height": info.get("height", 1080),
            }

    return await loop.run_in_executor(None, download)
