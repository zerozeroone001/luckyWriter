from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AIGenerationLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


class GenerationLogResponse(BaseModel):
    """AI 生成日志响应数据。"""

    id: int
    novel_id: int | None
    generation_type: str
    api_endpoint: str | None
    channel_name: str | None
    channel_provider: str | None
    model_name: str | None
    model_identifier: str | None
    request_params: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost: float | None
    duration_seconds: float | None
    status: str | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/generation-logs", response_model=list[GenerationLogResponse])
async def list_generation_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    generation_type: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """分页查询 AI 生成调用日志。"""
    query = select(AIGenerationLog)

    if generation_type:
        query = query.where(AIGenerationLog.generation_type == generation_type)
    if status:
        query = query.where(AIGenerationLog.status == status)

    result = await db.execute(
        query.order_by(desc(AIGenerationLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()
