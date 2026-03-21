from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_async_session
from app.storage.models import KnowledgeDB

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class CreateKnowledgeRequest(BaseModel):
    knowledge_type: str
    title: str
    content: str
    metadata: dict = {}


class KnowledgeResponse(BaseModel):
    id: str
    knowledge_type: str
    title: str
    content: str
    metadata: dict
    created_at: str
    updated_at: str


@router.post("", response_model=KnowledgeResponse)
async def create_knowledge(
    request: CreateKnowledgeRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    knowledge_id = str(uuid.uuid4())
    
    db_knowledge = KnowledgeDB(
        id=knowledge_id,
        knowledge_type=request.knowledge_type,
        title=request.title,
        content=request.content,
        metadata=request.metadata,
    )
    db_session.add(db_knowledge)
    await db_session.flush()
    
    return KnowledgeResponse(
        id=knowledge_id,
        knowledge_type=request.knowledge_type,
        title=request.title,
        content=request.content,
        metadata=request.metadata,
        created_at=db_knowledge.created_at.isoformat(),
        updated_at=db_knowledge.updated_at.isoformat(),
    )


@router.get("", response_model=List[KnowledgeResponse])
async def list_knowledge(
    knowledge_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_session: AsyncSession = Depends(get_async_session),
):
    query = select(KnowledgeDB).order_by(KnowledgeDB.created_at.desc())
    
    if knowledge_type:
        query = query.where(KnowledgeDB.knowledge_type == knowledge_type)
    
    query = query.limit(limit).offset(offset)
    
    result = await db_session.execute(query)
    knowledge_list = result.scalars().all()
    
    return [
        KnowledgeResponse(
            id=k.id,
            knowledge_type=k.knowledge_type,
            title=k.title,
            content=k.content,
            metadata=k.metadata,
            created_at=k.created_at.isoformat(),
            updated_at=k.updated_at.isoformat(),
        )
        for k in knowledge_list
    ]


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    result = await db_session.execute(
        select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
    )
    k = result.scalar_one_or_none()
    if not k:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return KnowledgeResponse(
        id=k.id,
        knowledge_type=k.knowledge_type,
        title=k.title,
        content=k.content,
        metadata=k.metadata,
        created_at=k.created_at.isoformat(),
        updated_at=k.updated_at.isoformat(),
    )
