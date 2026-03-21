from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    title: str
    content: Optional[str] = None
    type: Literal["text", "file"] = "text"
    tags: List[str] = []
    category: Optional[str] = None


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class Knowledge(KnowledgeBase):
    id: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    reference_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
