import os
import tempfile
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Knowledge, KnowledgeCreate, KnowledgeUpdate
from app.services.document_parser import is_allowed_file, parse_document, MAX_FILE_SIZE
from app.storage.database import get_async_session
from app.storage.models import KnowledgeDB

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class KnowledgeResponse(BaseModel):
    id: str
    knowledge_type: str
    title: str
    content: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None
    reference_count: int = 0
    created_at: str
    updated_at: str


@router.get("", response_model=List[KnowledgeResponse])
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    db_session: AsyncSession = Depends(get_async_session),
):
    query = select(KnowledgeDB).order_by(KnowledgeDB.created_at.desc())

    if type:
        query = query.where(KnowledgeDB.knowledge_type == type)

    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.where(KnowledgeDB.tags.contains([tag]))

    if search:
        query = query.where(KnowledgeDB.title.ilike(f"%{search}%"))

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db_session.execute(query)
    knowledge_list = result.scalars().all()

    return [_to_response(k) for k in knowledge_list]


@router.post("", response_model=KnowledgeResponse)
async def create_knowledge(
    data: KnowledgeCreate,
    db_session: AsyncSession = Depends(get_async_session),
):
    knowledge_id = str(uuid.uuid4())

    db_obj = KnowledgeDB(
        id=knowledge_id,
        knowledge_type=data.type,
        title=data.title,
        content=data.content,
        tags=data.tags,
        category=data.category,
    )
    db_session.add(db_obj)
    await db_session.commit()

    return _to_response(db_obj)


@router.get("/tags", response_model=List[str])
async def list_knowledge_tags(db_session: AsyncSession = Depends(get_async_session)):
    result = await db_session.execute(select(KnowledgeDB))
    all_knowledge = result.scalars().all()
    tags = set()
    for k in all_knowledge:
        if k.tags:
            tags.update(k.tags)
    return sorted(list(tags))


@router.post("/upload", response_model=KnowledgeResponse)
async def upload_knowledge(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    tags: Optional[str] = None,
    category: Optional[str] = None,
    db_session: AsyncSession = Depends(get_async_session),
):
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制(50MB)")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parsed_content, ext = parse_document(tmp_path, file.filename)
    finally:
        os.unlink(tmp_path)

    file_id = str(uuid.uuid4())
    file_url = f"/uploads/knowledge/{file_id}_{file.filename}"

    db_obj = KnowledgeDB(
        id=file_id,
        knowledge_type="file",
        title=title or file.filename,
        content=parsed_content,
        file_url=file_url,
        file_name=file.filename,
        tags=[t.strip() for t in tags.split(",")] if tags else [],
        category=category,
    )
    db_session.add(db_obj)
    await db_session.commit()

    return _to_response(db_obj)


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
        raise HTTPException(status_code=404, detail="知识不存在")
    return _to_response(k)


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    data: KnowledgeUpdate,
    db_session: AsyncSession = Depends(get_async_session),
):
    result = await db_session.execute(
        select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
    )
    db_obj = result.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="知识不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db_session.commit()
    return _to_response(db_obj)


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    result = await db_session.execute(
        select(KnowledgeDB).where(KnowledgeDB.id == knowledge_id)
    )
    db_obj = result.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="知识不存在")

    await db_session.delete(db_obj)
    await db_session.commit()
    return {"message": "删除成功"}


def _to_response(k: KnowledgeDB) -> KnowledgeResponse:
    return KnowledgeResponse(
        id=k.id,
        knowledge_type=k.knowledge_type,
        title=k.title,
        content=k.content,
        file_url=k.file_url,
        file_name=k.file_name,
        tags=k.tags or [],
        category=k.category,
        reference_count=k.reference_count or 0,
        created_at=k.created_at.isoformat(),
        updated_at=k.updated_at.isoformat(),
    )
