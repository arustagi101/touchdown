import os
import subprocess
import json
import tempfile
import asyncio
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import ffmpeg
import yt_dlp
from app.core.config import settings

class VideoProcessor:
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download_video(self, url: str, output_path: str) -> Dict:
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return {
                    'title': info.get('title', 'Untitled'),
                    'duration': info.get('duration', 0),
                    'fps': info.get('fps', 30),
                    'width': info.get('width', 1920),
                    'height': info.get('height', 1080),
                }

        return await loop.run_in_executor(None, download)

    async def get_video_info(self, video_path: str) -> Dict:
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

            if not video_stream:
                raise ValueError("No video stream found")

            return {
                'duration': float(probe['format']['duration']),
                'fps': eval(video_stream.get('r_frame_rate', '30/1')),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'codec': video_stream['codec_name'],
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'size': int(probe['format'].get('size', 0)),
            }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

    async def extract_audio(self, video_path: str, output_path: str) -> str:
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar='16000')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

            return output_path
        except Exception as e:
            raise Exception(f"Failed to extract audio: {str(e)}")

    async def extract_clip(self, video_path: str, start_time: float, end_time: float, output_path: str) -> str:
        try:
            duration = end_time - start_time
            stream = ffmpeg.input(video_path, ss=start_time, t=duration)
            stream = ffmpeg.output(stream, output_path, c='copy')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

            return output_path
        except Exception as e:
            raise Exception(f"Failed to extract clip: {str(e)}")

    async def concatenate_clips(self, clip_paths: List[str], output_path: str, transition: str = "fade") -> str:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for clip_path in clip_paths:
                    f.write(f"file '{clip_path}'\n")
                concat_file = f.name

            if transition == "none":
                stream = ffmpeg.input(concat_file, format='concat', safe=0)
                stream = ffmpeg.output(stream, output_path, c='copy')
            else:
                streams = []
                for clip_path in clip_paths:
                    stream = ffmpeg.input(clip_path)
                    streams.append(stream)

                if len(streams) > 1:
                    stream = ffmpeg.concat(*streams, v=1, a=1)
                else:
                    stream = streams[0]

                stream = ffmpeg.output(stream, output_path, vcodec='libx264', acodec='aac')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

            os.unlink(concat_file)
            return output_path
        except Exception as e:
            raise Exception(f"Failed to concatenate clips: {str(e)}")

    async def generate_thumbnail(self, video_path: str, output_path: str, time_position: float = None) -> str:
        try:
            if time_position is None:
                info = await self.get_video_info(video_path)
                time_position = info['duration'] / 2

            stream = ffmpeg.input(video_path, ss=time_position)
            stream = ffmpeg.output(stream, output_path, vframes=1)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

            return output_path
        except Exception as e:
            raise Exception(f"Failed to generate thumbnail: {str(e)}")

    async def add_watermark(self, video_path: str, watermark_path: str, output_path: str, position: str = "bottom-right") -> str:
        try:
            main = ffmpeg.input(video_path)
            watermark = ffmpeg.input(watermark_path)

            position_map = {
                "bottom-right": "overlay=W-w-10:H-h-10",
                "bottom-left": "overlay=10:H-h-10",
                "top-right": "overlay=W-w-10:10",
                "top-left": "overlay=10:10",
                "center": "overlay=(W-w)/2:(H-h)/2"
            }

            overlay_position = position_map.get(position, position_map["bottom-right"])

            stream = ffmpeg.filter([main, watermark], 'overlay', overlay_position)
            stream = ffmpeg.output(stream, output_path)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

            return output_path
        except Exception as e:
            raise Exception(f"Failed to add watermark: {str(e)}")

    def cleanup_temp_files(self, file_paths: List[str]):
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass