from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models import SystemPreset


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class SystemPromptCreate(BaseModel):
    name: str
    prompt_type: str = "default"
    prompt_role: str
    system_prompt: str
    use_case: Optional[str] = None


class SystemPromptUpdate(BaseModel):
    name: Optional[str] = None
    prompt_type: Optional[str] = None
    prompt_role: Optional[str] = None
    system_prompt: Optional[str] = None
    use_case: Optional[str] = None
    is_default: Optional[bool] = None


@router.get("/")
async def get_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset).order_by(SystemPreset.prompt_type, SystemPreset.use_case))
    return result.scalars().all()


@router.get("/roles")
async def get_prompt_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset.prompt_role).distinct())
    return [row[0] for row in result.all()]


@router.get("/types")
async def get_prompt_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset.prompt_type).distinct())
    return [row[0] for row in result.all()]


@router.get("/{prompt_id}")
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset).where(SystemPreset.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return prompt


@router.post("/")
async def create_prompt(data: SystemPromptCreate, db: AsyncSession = Depends(get_db)):
    prompt = SystemPreset(**data.model_dump())
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.put("/{prompt_id}")
async def update_prompt(prompt_id: int, data: SystemPromptUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset).where(SystemPreset.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prompt, key, value)

    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemPreset).where(SystemPreset.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")

    await db.delete(prompt)
    await db.commit()
    return {"message": "删除成功"}
