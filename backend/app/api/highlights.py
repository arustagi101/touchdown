from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models import Highlight, Video
from app.schemas.highlight import HighlightUpdate, HighlightResponse

router = APIRouter()

@router.patch("/{highlight_id}")
async def update_highlight(
    highlight_id: uuid.UUID,
    update_data: HighlightUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Highlight).where(Highlight.id == highlight_id))
    highlight = result.scalar_one_or_none()

    if not highlight:
        raise HTTPException(404, "Highlight not found")

    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(highlight, field, value)

    await db.commit()
    await db.refresh(highlight)

    return HighlightResponse.from_orm(highlight)

@router.post("/{video_id}/reorder")
async def reorder_highlights(
    video_id: uuid.UUID,
    highlight_order: List[str],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Highlight).where(Highlight.video_id == video_id)
    )
    highlights = result.scalars().all()

    if not highlights:
        raise HTTPException(404, "No highlights found for this video")

    highlight_map = {str(h.id): h for h in highlights}

    for index, highlight_id in enumerate(highlight_order):
        if highlight_id in highlight_map:
            highlight_map[highlight_id].order_index = index

    await db.commit()

    return {"message": "Highlights reordered successfully"}

@router.post("/{video_id}/auto-select")
async def auto_select_highlights(
    video_id: uuid.UUID,
    target_duration: int = 120,
    min_score: float = 60.0,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Highlight)
        .where(Highlight.video_id == video_id)
        .order_by(Highlight.score.desc())
    )
    highlights = result.scalars().all()

    if not highlights:
        raise HTTPException(404, "No highlights found for this video")

    selected_duration = 0
    selected_highlights = []

    for highlight in highlights:
        if highlight.score < min_score:
            break

        if selected_duration + highlight.duration <= target_duration:
            highlight.is_included = True
            selected_highlights.append(highlight)
            selected_duration += highlight.duration
        else:
            highlight.is_included = False

    await db.commit()

    return {
        "selected_count": len(selected_highlights),
        "total_duration": selected_duration,
        "highlight_ids": [str(h.id) for h in selected_highlights]
    }

@router.delete("/{highlight_id}")
async def delete_highlight(
    highlight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Highlight).where(Highlight.id == highlight_id))
    highlight = result.scalar_one_or_none()

    if not highlight:
        raise HTTPException(404, "Highlight not found")

    await db.delete(highlight)
    await db.commit()

    return {"message": "Highlight deleted successfully"}