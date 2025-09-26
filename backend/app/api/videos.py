from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import uuid
import os
import aiofiles
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models import Video, Transcript, Highlight
from app.schemas.video import VideoCreate, VideoResponse, VideoStatus
from app.services.video_processor import VideoProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.tasks.video_tasks import process_video_task

router = APIRouter()

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    sport_type: Optional[str] = "general",
    db: AsyncSession = Depends(get_db)
):
    if file.size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File size exceeds {settings.MAX_VIDEO_SIZE_MB}MB limit")

    video_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1]
    local_path = Path(settings.TEMP_DIR) / f"{video_id}.{file_extension}"

    async with aiofiles.open(local_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    video = Video(
        id=video_id,
        title=title or file.filename,
        local_path=str(local_path),
        sport_type=sport_type,
        video_type="upload",
        status="pending"
    )
    db.add(video)
    await db.commit()

    background_tasks.add_task(process_video_task, video_id)

    return VideoResponse.from_orm(video)

@router.post("/from-url", response_model=VideoResponse)
async def process_from_url(
    url: str,
    title: Optional[str] = None,
    sport_type: Optional[str] = "general",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    video_id = str(uuid.uuid4())

    video_type = "youtube" if "youtube.com" in url or "youtu.be" in url else "url"

    video = Video(
        id=video_id,
        title=title or "Video from URL",
        original_url=url,
        sport_type=sport_type,
        video_type=video_type,
        status="pending"
    )
    db.add(video)
    await db.commit()

    background_tasks.add_task(process_video_task, video_id)

    return VideoResponse.from_orm(video)

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(404, "Video not found")

    return VideoResponse.from_orm(video)

@router.get("/{video_id}/status")
async def get_video_status(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(404, "Video not found")

    return {
        "status": video.status,
        "progress": video.processing_progress,
        "error_message": video.error_message
    }

@router.get("/{video_id}/transcript")
async def get_transcript(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transcript).where(Transcript.video_id == video_id)
    )
    transcript = result.scalar_one_or_none()

    if not transcript:
        raise HTTPException(404, "Transcript not found")

    return {
        "text": transcript.full_text,
        "segments": transcript.segments,
        "language": transcript.language
    }

@router.get("/{video_id}/highlights")
async def get_highlights(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Highlight)
        .where(Highlight.video_id == video_id)
        .order_by(Highlight.score.desc())
    )
    highlights = result.scalars().all()

    return [{
        "id": str(h.id),
        "start_time": h.start_time,
        "end_time": h.end_time,
        "duration": h.duration,
        "score": h.score,
        "category": h.category,
        "description": h.description,
        "is_included": h.is_included,
        "order_index": h.order_index
    } for h in highlights]

@router.post("/{video_id}/generate-reel")
async def generate_highlight_reel(
    video_id: uuid.UUID,
    highlight_ids: Optional[List[str]] = None,
    max_duration: Optional[int] = 180,
    include_transitions: bool = True,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(404, "Video not found")

    if video.status != "completed":
        raise HTTPException(400, "Video processing not completed")

    background_tasks.add_task(
        generate_reel_task,
        video_id,
        highlight_ids,
        max_duration,
        include_transitions
    )

    return {"message": "Highlight reel generation started", "video_id": str(video_id)}

@router.delete("/{video_id}")
async def delete_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(404, "Video not found")

    if video.local_path and os.path.exists(video.local_path):
        os.remove(video.local_path)

    await db.delete(video)
    await db.commit()

    return {"message": "Video deleted successfully"}

async def generate_reel_task(video_id: str, highlight_ids: List[str], max_duration: int, include_transitions: bool):
    pass