from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base


class SessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trigger_type: Mapped[str] = mapped_column(String(50))
    trigger_source: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), index=True)
    investigation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    root_cause: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recovery_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    execution_results: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class EvidenceDB(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    evidence_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    source_data: Mapped[dict] = mapped_column(JSON)
    source_system: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class KnowledgeDB(Base):
    __tablename__ = "knowledge"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_type: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
