from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Novel, Chapter


router = APIRouter(prefix="/api/novels", tags=["novels"])


# Pydantic模型
class NovelCreate(BaseModel):
    title: str
    author: str = "默认作者"
    genre: Optional[str] = None
    target_words: int = 1000000
    synopsis: Optional[str] = None


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    target_words: Optional[int] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None
    cover_image: Optional[str] = None


class NovelResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: Optional[str]
    target_words: int
    current_words: int
    cover_image: Optional[str]
    synopsis: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=NovelResponse)
async def create_novel(
    novel_data: NovelCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新小说"""
    novel = Novel(**novel_data.model_dump())
    db.add(novel)
    await db.commit()
    await db.refresh(novel)
    return novel


@router.get("", response_model=List[NovelResponse])
async def list_novels(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """获取小说列表"""
    result = await db.execute(
        select(Novel)
        .order_by(Novel.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    novels = result.scalars().all()
    return novels


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取小说详情"""
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    return novel


@router.put("/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: int,
    novel_data: NovelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新小说信息"""
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    # 更新字段
    for field, value in novel_data.model_dump(exclude_unset=True).items():
        setattr(novel, field, value)

    await db.commit()
    await db.refresh(novel)
    return novel


@router.delete("/{novel_id}")
async def delete_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除小说"""
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    await db.delete(novel)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/{novel_id}/stats")
async def get_novel_stats(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取小说统计信息"""
    # 检查小说是否存在
    result = await db.execute(
        select(Novel).where(Novel.id == novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    # 统计章节数
    chapter_count_result = await db.execute(
        select(func.count(Chapter.id)).where(Chapter.novel_id == novel_id)
    )
    chapter_count = chapter_count_result.scalar()

    # 统计总字数
    word_count_result = await db.execute(
        select(func.sum(Chapter.word_count)).where(Chapter.novel_id == novel_id)
    )
    total_words = word_count_result.scalar() or 0

    # 更新小说当前字数
    novel.current_words = total_words
    await db.commit()

    return {
        "novel_id": novel_id,
        "chapter_count": chapter_count,
        "total_words": total_words,
        "target_words": novel.target_words,
        "progress": round(total_words / novel.target_words * 100, 2) if novel.target_words > 0 else 0,
    }
