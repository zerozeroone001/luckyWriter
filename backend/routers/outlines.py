from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Novel, Outline


router = APIRouter(prefix="/api/outlines", tags=["outlines"])


class OutlineBase(BaseModel):
    volume_number: Optional[int] = None
    chapter_number: Optional[int] = None
    title: Optional[str] = None
    plot_summary: Optional[str] = None
    key_events: Optional[str] = None
    characters_involved: Optional[str] = None
    outline_type: Optional[str] = "chapter"

    @field_validator("volume_number", "chapter_number")
    @classmethod
    def validate_positive_number(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("卷号和章节号必须大于 0")
        return value

    @field_validator("outline_type")
    @classmethod
    def validate_outline_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"volume", "chapter", "scene"}:
            raise ValueError("大纲类型只能是 volume、chapter 或 scene")
        return value


class OutlineCreate(OutlineBase):
    novel_id: int
    title: str


class OutlineUpdate(OutlineBase):
    pass


class OutlineResponse(BaseModel):
    id: int
    novel_id: int
    volume_number: Optional[int]
    chapter_number: Optional[int]
    title: str
    plot_summary: Optional[str]
    key_events: Optional[str]
    characters_involved: Optional[str]
    outline_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


async def ensure_novel_exists(db: AsyncSession, novel_id: int) -> None:
    """确认小说存在。"""
    result = await db.execute(select(Novel.id).where(Novel.id == novel_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="小说不存在")


@router.get("/novel/{novel_id}", response_model=List[OutlineResponse])
async def list_outlines_by_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取指定小说的大纲列表。"""
    await ensure_novel_exists(db, novel_id)

    result = await db.execute(
        select(Outline)
        .where(Outline.novel_id == novel_id)
        .order_by(
            Outline.volume_number.is_(None),
            Outline.volume_number.asc(),
            Outline.chapter_number.is_(None),
            Outline.chapter_number.asc(),
            Outline.id.asc(),
        )
    )
    return result.scalars().all()


@router.post("", response_model=OutlineResponse)
async def create_outline(
    outline_data: OutlineCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建大纲项。"""
    await ensure_novel_exists(db, outline_data.novel_id)

    payload = outline_data.model_dump()
    payload["title"] = payload["title"].strip()
    if not payload["title"]:
        raise HTTPException(status_code=422, detail="大纲标题不能为空")

    outline = Outline(**payload)
    db.add(outline)
    await db.commit()
    await db.refresh(outline)
    return outline


@router.put("/{outline_id}", response_model=OutlineResponse)
async def update_outline(
    outline_id: int,
    outline_data: OutlineUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新大纲项。"""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()

    if not outline:
        raise HTTPException(status_code=404, detail="大纲不存在")

    payload = outline_data.model_dump(exclude_unset=True)
    if "title" in payload:
        payload["title"] = payload["title"].strip() if payload["title"] else ""
        if not payload["title"]:
            raise HTTPException(status_code=422, detail="大纲标题不能为空")

    for field, value in payload.items():
        setattr(outline, field, value)

    await db.commit()
    await db.refresh(outline)
    return outline


@router.delete("/{outline_id}")
async def delete_outline(
    outline_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除大纲项。"""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()

    if not outline:
        raise HTTPException(status_code=404, detail="大纲不存在")

    await db.delete(outline)
    await db.commit()
    return {"message": "删除成功"}
