from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import time

from database import get_db
from models import AIChannel, AIModel
from services.ai_service import ai_service


router = APIRouter(prefix="/api/channels", tags=["channels"])


# Pydantic模型
class AIChannelCreate(BaseModel):
    name: str
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class AIChannelUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_enabled: Optional[bool] = None


class AIChannelResponse(BaseModel):
    id: int
    name: str
    provider: str
    base_url: Optional[str]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    model_count: int = 0

    class Config:
        from_attributes = True


class AIModelCreate(BaseModel):
    channel_id: int
    model_name: str
    model_id: str
    temperature: float = 0.8
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0


class AIModelUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    temperature: Optional[float] = None
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None


class AIModelResponse(BaseModel):
    id: int
    channel_id: int
    model_name: str
    model_id: str
    is_enabled: bool
    temperature: float
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    response_time_ms: Optional[int]
    last_test_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailableModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


# ============ 渠道管理 ============

@router.post("", response_model=AIChannelResponse)
async def create_channel(
    channel_data: AIChannelCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建AI渠道"""
    channel = AIChannel(**channel_data.model_dump())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    # 添加model_count字段
    response = AIChannelResponse.model_validate(channel)
    response.model_count = 0
    return response


@router.get("", response_model=List[AIChannelResponse])
async def list_channels(
    db: AsyncSession = Depends(get_db),
):
    """获取所有AI渠道"""
    result = await db.execute(
        select(AIChannel).order_by(AIChannel.created_at.desc())
    )
    channels = result.scalars().all()

    # 查询每个渠道的模型数量
    responses = []
    for channel in channels:
        model_count_result = await db.execute(
            select(AIModel).where(AIModel.channel_id == channel.id)
        )
        model_count = len(model_count_result.scalars().all())

        response = AIChannelResponse.model_validate(channel)
        response.model_count = model_count
        responses.append(response)

    return responses


@router.get("/{channel_id}", response_model=AIChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取AI渠道详情"""
    result = await db.execute(
        select(AIChannel).where(AIChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="AI渠道不存在")

    # 查询模型数量
    model_count_result = await db.execute(
        select(AIModel).where(AIModel.channel_id == channel_id)
    )
    model_count = len(model_count_result.scalars().all())

    response = AIChannelResponse.model_validate(channel)
    response.model_count = model_count
    return response


@router.put("/{channel_id}", response_model=AIChannelResponse)
async def update_channel(
    channel_id: int,
    channel_data: AIChannelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新AI渠道"""
    result = await db.execute(
        select(AIChannel).where(AIChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="AI渠道不存在")

    # 更新字段
    for field, value in channel_data.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    # 查询模型数量
    model_count_result = await db.execute(
        select(AIModel).where(AIModel.channel_id == channel_id)
    )
    model_count = len(model_count_result.scalars().all())

    response = AIChannelResponse.model_validate(channel)
    response.model_count = model_count
    return response


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除AI渠道"""
    result = await db.execute(
        select(AIChannel).where(AIChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="AI渠道不存在")

    await db.delete(channel)
    await db.commit()

    return {"message": "删除成功"}


# ============ 获取可用模型 ============

@router.get("/{channel_id}/available-models", response_model=List[AvailableModel])
async def get_available_models(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取渠道支持的模型列表"""
    result = await db.execute(
        select(AIChannel).where(AIChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="AI渠道不存在")

    try:
        models = await ai_service.get_available_models(
            provider=channel.provider,
            api_key=channel.api_key,
            base_url=channel.base_url,
        )
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


# ============ 模型管理 ============

@router.post("/models", response_model=AIModelResponse)
async def create_model(
    model_data: AIModelCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加模型"""
    # 检查渠道是否存在
    channel_result = await db.execute(
        select(AIChannel).where(AIChannel.id == model_data.channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="AI渠道不存在")

    model = AIModel(**model_data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.get("/{channel_id}/models", response_model=List[AIModelResponse])
async def list_models(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取渠道的所有模型"""
    result = await db.execute(
        select(AIModel)
        .where(AIModel.channel_id == channel_id)
        .order_by(AIModel.created_at.desc())
    )
    models = result.scalars().all()
    return models


@router.put("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    model_data: AIModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新模型配置"""
    result = await db.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    for field, value in model_data.model_dump(exclude_unset=True).items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除模型"""
    result = await db.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    await db.delete(model)
    await db.commit()

    return {"message": "删除成功"}


# ============ 模型测速 ============

@router.post("/models/{model_id}/test-speed")
async def test_model_speed(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """测试模型响应速度"""
    # 获取模型信息
    model_result = await db.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = model_result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    # 获取渠道信息
    channel_result = await db.execute(
        select(AIChannel).where(AIChannel.id == model.channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    try:
        # 测试模型响应速度
        start_time = time.time()

        await ai_service.test_model_speed(
            provider=channel.provider,
            model=model.model_id,
            api_key=channel.api_key,
            base_url=channel.base_url,
        )

        response_time_ms = int((time.time() - start_time) * 1000)

        # 更新模型响应时间
        model.response_time_ms = response_time_ms
        model.last_test_at = datetime.now()
        await db.commit()
        await db.refresh(model)

        return {
            "model_id": model_id,
            "response_time_ms": response_time_ms,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测速失败: {str(e)}")
