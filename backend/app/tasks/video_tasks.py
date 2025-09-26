import asyncio
import os
from pathlib import Path
from typing import List, Dict
import uuid

from app.core.database import AsyncSessionLocal
from app.models import Video, Transcript, Highlight
from app.services.video_processor import VideoProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.core.websocket import notify_video_progress, notify_video_completed, notify_video_error
from sqlalchemy import select

async def process_video_task(video_id: str):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()

            if not video:
                return

            processor = VideoProcessor()
            analyzer = AIAnalyzer()

            video.status = "downloading"
            video.processing_progress = 10
            await db.commit()
            await notify_video_progress(video_id, "downloading", 10, "Downloading video...")

            if video.original_url:
                local_path = Path(processor.temp_dir) / f"{video_id}.mp4"
                video_info = await processor.download_video(video.original_url, str(local_path))
                video.local_path = str(local_path)
                video.title = video_info.get('title', video.title)
                video.duration = video_info.get('duration')
                video.fps = video_info.get('fps')
                video.width = video_info.get('width')
                video.height = video_info.get('height')
            else:
                video_info = await processor.get_video_info(video.local_path)
                video.duration = video_info.get('duration')
                video.fps = video_info.get('fps')
                video.width = video_info.get('width')
                video.height = video_info.get('height')

            video.status = "transcribing"
            video.processing_progress = 30
            await db.commit()
            await notify_video_progress(video_id, "transcribing", 30, "Extracting audio and transcribing...")

            audio_path = Path(processor.temp_dir) / f"{video_id}.wav"
            await processor.extract_audio(video.local_path, str(audio_path))

            transcript_data = await analyzer.transcribe_audio(str(audio_path))

            transcript = Transcript(
                video_id=video_id,
                full_text=transcript_data['text'],
                segments=transcript_data['segments'],
                language=transcript_data.get('language', 'en')
            )
            db.add(transcript)

            video.status = "analyzing"
            video.processing_progress = 60
            await db.commit()
            await notify_video_progress(video_id, "analyzing", 60, "Analyzing for highlights...")

            highlights_data = await analyzer.analyze_highlights(
                transcript_data,
                sport_type=video.sport_type,
                num_highlights=15
            )

            for idx, highlight_data in enumerate(highlights_data):
                highlight = Highlight(
                    video_id=video_id,
                    start_time=highlight_data['start_time'],
                    end_time=highlight_data['end_time'],
                    duration=highlight_data['duration'],
                    score=highlight_data['score'],
                    category=highlight_data['category'],
                    description=highlight_data['description'],
                    transcript_segment=highlight_data.get('transcript_segment'),
                    order_index=idx,
                    is_included=idx < 10
                )
                db.add(highlight)

            video.status = "completed"
            video.processing_progress = 100
            await db.commit()
            await notify_video_completed(video_id, len(highlights_data))

            if os.path.exists(str(audio_path)):
                os.remove(str(audio_path))

        except Exception as e:
            video.status = "failed"
            video.error_message = str(e)
            await db.commit()
            await notify_video_error(video_id, str(e))

async def generate_highlight_reel_task(
    video_id: str,
    highlight_ids: List[str] = None,
    max_duration: int = 180,
    include_transitions: bool = True
):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()

            if not video:
                return

            processor = VideoProcessor()

            await notify_video_progress(video_id, "generating", 0, "Starting highlight reel generation...")

            if highlight_ids:
                result = await db.execute(
                    select(Highlight)
                    .where(Highlight.video_id == video_id)
                    .where(Highlight.id.in_(highlight_ids))
                    .order_by(Highlight.order_index)
                )
            else:
                result = await db.execute(
                    select(Highlight)
                    .where(Highlight.video_id == video_id)
                    .where(Highlight.is_included == True)
                    .order_by(Highlight.order_index)
                )

            highlights = result.scalars().all()

            if not highlights:
                raise Exception("No highlights selected for reel generation")

            clip_paths = []
            total_duration = 0

            for idx, highlight in enumerate(highlights):
                if total_duration + highlight.duration > max_duration:
                    break

                clip_path = Path(processor.temp_dir) / f"{video_id}_clip_{idx}.mp4"
                await processor.extract_clip(
                    video.local_path,
                    highlight.start_time,
                    highlight.end_time,
                    str(clip_path)
                )
                clip_paths.append(str(clip_path))
                total_duration += highlight.duration

                progress = int((idx + 1) / len(highlights) * 50)
                await notify_video_progress(
                    video_id,
                    "generating",
                    progress,
                    f"Extracting clip {idx + 1}/{len(highlights)}..."
                )

            await notify_video_progress(video_id, "generating", 60, "Concatenating clips...")

            reel_path = Path(processor.temp_dir) / f"{video_id}_highlights.mp4"
            transition_type = "fade" if include_transitions else "none"
            await processor.concatenate_clips(clip_paths, str(reel_path), transition_type)

            await notify_video_progress(video_id, "generating", 80, "Generating thumbnail...")

            thumbnail_path = Path(processor.temp_dir) / f"{video_id}_thumbnail.jpg"
            best_highlight = max(highlights, key=lambda h: h.score)
            await processor.generate_thumbnail(
                video.local_path,
                str(thumbnail_path),
                (best_highlight.start_time + best_highlight.end_time) / 2
            )

            processor.cleanup_temp_files(clip_paths)

            await notify_video_progress(video_id, "generating", 100, "Highlight reel completed!")
            await notify_video_completed(video_id, len(clip_paths))

            return str(reel_path)

        except Exception as e:
            await notify_video_error(video_id, f"Reel generation failed: {str(e)}")