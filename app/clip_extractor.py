
import asyncio
import ffmpeg


async def extract_clip(video_path: str, start_time: float, end_time: float, output_path: str) -> str:
    try:
        duration = end_time - start_time
        stream = ffmpeg.input(video_path, ss=start_time, t=duration)
        stream = ffmpeg.output(stream, output_path, c='copy')

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True))

        return output_path
    except Exception as e:
        raise Exception(f"Failed to extract clip: {str(e)}")