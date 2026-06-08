from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Character


router = APIRouter(prefix="/api/characters", tags=["characters"])


# Pydantic模型
class CharacterCreate(BaseModel):
    novel_id: int
    name: str
    gender: Optional[str] = None
    age: Optional[str] = None
    appearance: Optional[str] = None
    identity_info: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    relationships: Optional[str] = None
    abilities: Optional[str] = None
    character_arc: Optional[str] = None
    quotes: Optional[str] = None
    avatar_url: Optional[str] = None
    importance: str = "minor"


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    appearance: Optional[str] = None
    identity_info: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    relationships: Optional[str] = None
    abilities: Optional[str] = None
    character_arc: Optional[str] = None
    quotes: Optional[str] = None
    avatar_url: Optional[str] = None
    importance: Optional[str] = None


class CharacterResponse(BaseModel):
    id: int
    novel_id: int
    name: str
    gender: Optional[str]
    age: Optional[str]
    appearance: Optional[str]
    identity_info: Optional[str]
    personality: Optional[str]
    background: Optional[str]
    relationships: Optional[str]
    abilities: Optional[str]
    character_arc: Optional[str]
    quotes: Optional[str]
    avatar_url: Optional[str]
    importance: str
    is_detailed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=CharacterResponse)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新角色"""
    character = Character(**character_data.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.get("/novel/{novel_id}", response_model=List[CharacterResponse])
async def list_characters_by_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取小说的所有角色"""
    result = await db.execute(
        select(Character)
        .where(Character.novel_id == novel_id)
        .order_by(
            Character.importance.desc(),
            Character.created_at
        )
    )
    characters = result.scalars().all()
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取角色详情"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    character_data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新角色"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 更新字段
    for field, value in character_data.model_dump(exclude_unset=True).items():
        setattr(character, field, value)

    await db.commit()
    await db.refresh(character)
    return character


@router.delete("/{character_id}")
async def delete_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除角色"""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    await db.delete(character)
    await db.commit()

    return {"message": "删除成功"}
