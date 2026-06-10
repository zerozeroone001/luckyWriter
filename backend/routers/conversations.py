from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import json

from database import get_db
from models import InspirationConversation


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str
    messages: list[dict[str, str]]


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[list[dict[str, str]]] = None


@router.get("")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """获取对话列表"""
    result = await db.execute(
        select(InspirationConversation).order_by(InspirationConversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """获取对话详情"""
    result = await db.execute(
        select(InspirationConversation).where(InspirationConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": json.loads(conversation.messages),
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.post("")
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建对话"""
    conversation = InspirationConversation(
        title=request.title,
        messages=json.dumps(request.messages, ensure_ascii=False),
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return {"id": conversation.id}


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新对话"""
    result = await db.execute(
        select(InspirationConversation).where(InspirationConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if request.title is not None:
        conversation.title = request.title
    if request.messages is not None:
        conversation.messages = json.dumps(request.messages, ensure_ascii=False)
    
    await db.commit()
    return {"id": conversation.id}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """删除对话"""
    result = await db.execute(
        select(InspirationConversation).where(InspirationConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    await db.delete(conversation)
    await db.commit()
    return {"message": "删除成功"}
