from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Chapter


router = APIRouter(prefix="/api/chapters", tags=["chapters"])


# Pydantic模型
class ChapterCreate(BaseModel):
    novel_id: int
    volume_number: int = 1
    chapter_number: int
    title: str
    content: Optional[str] = None


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ChapterResponse(BaseModel):
    id: int
    novel_id: int
    volume_number: int
    chapter_number: int
    title: str
    content: Optional[str]
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ChapterResponse)
async def create_chapter(
    chapter_data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新章节"""
    chapter = Chapter(**chapter_data.model_dump())

    # 计算字数
    if chapter.content:
        chapter.word_count = len(chapter.content)

    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter


@router.get("/novel/{novel_id}", response_model=List[ChapterResponse])
async def list_chapters_by_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取小说的所有章节"""
    result = await db.execute(
        select(Chapter)
        .where(Chapter.novel_id == novel_id)
        .order_by(Chapter.volume_number, Chapter.chapter_number)
    )
    chapters = result.scalars().all()
    return chapters


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取章节详情"""
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    return chapter


@router.put("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新章节"""
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 更新字段
    for field, value in chapter_data.model_dump(exclude_unset=True).items():
        setattr(chapter, field, value)

    # 重新计算字数
    if chapter.content:
        chapter.word_count = len(chapter.content)

    await db.commit()
    await db.refresh(chapter)
    return chapter


@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除章节"""
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    await db.delete(chapter)
    await db.commit()

    return {"message": "删除成功"}
