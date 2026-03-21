# NyxAI 多Agent协作运维智能体实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个多Agent协作的运维智能体系统，支持故障自愈、可信推理、知识管理

**Architecture:** 分层协作架构 - 前端(React)直接与后端服务层(FastAPI+PydanticAI)通信，后端包含Orchestrator编排Agent和三个专业Agent(调查、根因定界、恢复)，通过工具层访问观测数据和知识库

**Tech Stack:** Python + FastAPI + PydanticAI / React + Ant Design / PostgreSQL + SQLite / Chroma / uv

**Spec:** [设计文档](../specs/2026-03-21-nyxai-ops-agent-design.md)

---

## 文件结构

```
NyxAI/
├── backend/
│   ├── pyproject.toml              # uv项目配置
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI入口
│   │   ├── config.py               # 配置管理
│   │   ├── dependencies.py         # 依赖注入
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Agent基类
│   │   │   ├── orchestrator.py     # 编排Agent
│   │   │   ├── investigation.py    # 调查Agent
│   │   │   ├── diagnosis.py        # 根因定界Agent
│   │   │   └── recovery.py         # 恢复Agent
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── prometheus.py
│   │   │   ├── influxdb.py
│   │   │   ├── loki.py
│   │   │   ├── jaeger.py
│   │   │   └── knowledge.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── evidence.py
│   │   │   ├── knowledge.py
│   │   │   └── api.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py
│   │   │   ├── chat.py
│   │   │   ├── knowledge.py
│   │   │   └── webhook.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py
│   │   │   ├── vector_store.py
│   │   │   └── scheduler.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── session.py
│   │   │       ├── evidence.py
│   │   │       └── knowledge.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_agents/
│   │   ├── test_tools/
│   │   └── test_api/
│   └── alembic/
│       └── versions/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── stores/
│   │   └── types/
│   └── vite.config.ts
└── docker-compose.yml
```

---

## Phase 1: 后端核心框架

### Task 1.1: 项目初始化

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/app/__init__.py`

- [ ] **Step 1: 初始化uv项目**

```bash
cd backend
uv init --name nyxai-backend
```

- [ ] **Step 2: 配置pyproject.toml**

```toml
[project]
name = "nyxai-backend"
version = "0.1.0"
description = "NyxAI Multi-Agent Ops System Backend"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-ai>=0.0.14",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "chromadb>=0.5.0",
    "httpx>=0.28.0",
    "python-multipart>=0.0.18",
    "websockets>=14.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: 安装依赖**

```bash
cd backend
uv sync --all-extras
```

- [ ] **Step 4: 创建基础目录结构**

```bash
mkdir -p backend/app/{agents,tools,models,api,services,storage/repositories,utils}
mkdir -p backend/tests/{test_agents,test_tools,test_api}
mkdir -p backend/alembic/versions
touch backend/app/__init__.py
touch backend/app/{agents,tools,models,api,services,storage,storage/repositories,utils}/__init__.py
touch backend/tests/__init__.py
touch backend/tests/{test_agents,test_tools,test_api}/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "chore: initialize backend project with uv"
```

---

### Task 1.2: 配置管理

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/tests/test_api/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_config.py
import pytest
from app.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.APP_NAME == "NyxAI"
    assert settings.DEBUG is False
    assert settings.DATABASE_URL is not None


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    settings = Settings()
    assert settings.DEBUG is True
    assert "test.db" in settings.DATABASE_URL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.config'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/config.py
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "NyxAI"
    DEBUG: bool = False
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./nyxai.db"
    
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    PROMETHEUS_URL: Optional[str] = None
    INFLUXDB_URL: Optional[str] = None
    INFLUXDB_TOKEN: Optional[str] = None
    LOKI_URL: Optional[str] = None
    JAEGER_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Add pydantic-settings dependency and run test**

```bash
cd backend
uv add pydantic-settings
uv run pytest tests/test_api/test_config.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_api/test_config.py backend/pyproject.toml backend/uv.lock
git commit -m "feat: add configuration management with pydantic-settings"
```

---

### Task 1.3: 日志工具

**Files:**
- Create: `backend/app/utils/logger.py`
- Create: `backend/tests/test_api/test_logger.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_logger.py
import logging
from app.utils.logger import get_logger, setup_logging


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


def test_setup_logging_configures_root_logger():
    setup_logging(level="DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_logger.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/utils/logger.py
import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    return logger
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_logger.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/logger.py backend/tests/test_api/test_logger.py
git commit -m "feat: add logging utility"
```

---

### Task 1.4: 数据库连接

**Files:**
- Create: `backend/app/storage/database.py`
- Create: `backend/tests/test_api/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_database.py
import pytest
from sqlalchemy import text
from app.storage.database import get_async_session, async_engine, Base


@pytest.mark.asyncio
async def test_database_connection():
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_get_async_session():
    async for session in get_async_session():
        assert session is not None
        break
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/storage/database.py
from collections.abc import AsyncGenerator
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/database.py backend/tests/test_api/test_database.py
git commit -m "feat: add async database connection with SQLAlchemy"
```

---

### Task 1.5: 核心数据模型 - Evidence

**Files:**
- Create: `backend/app/models/evidence.py`
- Create: `backend/tests/test_api/test_evidence_model.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_evidence_model.py
from datetime import datetime
from app.models.evidence import Evidence, EvidenceType, EvidenceNode


def test_evidence_creation():
    evidence = Evidence(
        id="ev-001",
        evidence_type=EvidenceType.METRIC,
        description="CPU usage 95%",
        source_data={"value": 95, "threshold": 80},
        source_system="prometheus",
        timestamp=datetime.now(),
        confidence=0.9,
    )
    assert evidence.id == "ev-001"
    assert evidence.evidence_type == EvidenceType.METRIC
    assert evidence.confidence == 0.9


def test_evidence_node_creation():
    evidence = Evidence(
        id="ev-001",
        evidence_type=EvidenceType.METRIC,
        description="CPU high",
        source_data={},
        source_system="prometheus",
        timestamp=datetime.now(),
        confidence=0.9,
    )
    node = EvidenceNode(
        id="node-001",
        description="High CPU leads to slow response",
        evidence=evidence,
        inference_step="CPU usage correlates with response time",
    )
    assert node.id == "node-001"
    assert len(node.supports) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_evidence_model.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/models/evidence.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    KNOWLEDGE = "knowledge"


class Evidence(BaseModel):
    id: str = Field(..., description="Evidence unique identifier")
    evidence_type: EvidenceType
    description: str = Field(..., description="Evidence description")
    source_data: Dict[str, Any] = Field(..., description="Raw data")
    source_system: str = Field(..., description="Source system")
    timestamp: datetime
    confidence: float = Field(..., ge=0, le=1, description="Evidence confidence")


class EvidenceNode(BaseModel):
    id: str
    description: str
    evidence: Evidence
    supports: List[str] = Field(default_factory=list, description="Supporting evidence node IDs")
    contradicts: List[str] = Field(default_factory=list, description="Contradicting evidence node IDs")
    inference_step: str = Field(..., description="Inference step explanation")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_evidence_model.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/evidence.py backend/tests/test_api/test_evidence_model.py
git commit -m "feat: add Evidence and EvidenceNode models"
```

---

### Task 1.6: 核心数据模型 - Session

**Files:**
- Create: `backend/app/models/session.py`
- Create: `backend/tests/test_api/test_session_model.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_session_model.py
from datetime import datetime
from app.models.session import Session, SessionStatus, RiskLevel, Anomaly


def test_session_creation():
    session = Session(
        id="sess-001",
        trigger_type="webhook",
        trigger_source="prometheus-alert",
        status=SessionStatus.INVESTIGATING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert session.id == "sess-001"
    assert session.status == SessionStatus.INVESTIGATING
    assert session.investigation is None


def test_anomaly_creation():
    anomaly = Anomaly(
        id="anom-001",
        component="mysql-primary",
        anomaly_type="high_cpu",
        severity="high",
        evidence_ids=["ev-001"],
        detected_at=datetime.now(),
    )
    assert anomaly.component == "mysql-primary"
    assert anomaly.severity == "high"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_session_model.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/models/session.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.evidence import Evidence, EvidenceNode


class SessionStatus(str, Enum):
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Anomaly(BaseModel):
    id: str
    component: str = Field(..., description="Anomalous component")
    anomaly_type: str = Field(..., description="Anomaly type")
    severity: str = Field(..., description="Severity level")
    evidence_ids: List[str] = Field(..., description="Related evidence IDs")
    detected_at: datetime


class InvestigationResult(BaseModel):
    session_id: str
    anomalies: List[Anomaly]
    evidence: List[Evidence]
    summary: str = Field(..., description="Investigation summary")
    created_at: datetime


class RootCauseAnalysis(BaseModel):
    session_id: str
    root_cause: str = Field(..., description="Root cause description")
    confidence: float = Field(..., ge=0, le=1)
    evidence_chain: List[EvidenceNode] = Field(..., description="Evidence chain")
    affected_components: List[str]
    reasoning_report: str = Field(..., description="Reasoning report")
    similar_cases: List[str] = Field(default_factory=list, description="Similar case IDs")
    created_at: datetime


class RecoveryAction(BaseModel):
    id: str
    action_type: str
    target: str
    params: Dict[str, Any]
    description: str
    risk_level: RiskLevel
    evidence_based: bool = Field(..., description="Whether based on evidence")
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class RecoveryPlan(BaseModel):
    session_id: str
    actions: List[RecoveryAction]
    overall_risk_level: RiskLevel
    requires_confirmation: bool
    rollback_plan: Optional[str]
    estimated_impact: str


class Session(BaseModel):
    id: str
    trigger_type: str = Field(..., description="Trigger type: webhook/scheduled/chat")
    trigger_source: str = Field(..., description="Trigger source")
    status: SessionStatus
    investigation: Optional[InvestigationResult] = None
    root_cause: Optional[RootCauseAnalysis] = None
    recovery_plan: Optional[RecoveryPlan] = None
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_session_model.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/session.py backend/tests/test_api/test_session_model.py
git commit -m "feat: add Session and related models"
```

---

### Task 1.7: 数据库表模型

**Files:**
- Create: `backend/app/storage/models.py`
- Create: `backend/tests/test_api/test_db_models.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_db_models.py
import pytest
from sqlalchemy import select
from app.storage.database import Base, async_engine, async_session_factory
from app.storage.models import SessionDB, EvidenceDB


@pytest.mark.asyncio
async def test_session_db_creation():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_factory() as session:
        db_session = SessionDB(
            id="test-sess-001",
            trigger_type="webhook",
            trigger_source="test",
            status="investigating",
        )
        session.add(db_session)
        await session.commit()
        
        result = await session.execute(
            select(SessionDB).where(SessionDB.id == "test-sess-001")
        )
        found = result.scalar_one()
        assert found.trigger_type == "webhook"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_db_models.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/storage/models.py
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Float, String, Text, func
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_db_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/models.py backend/tests/test_api/test_db_models.py
git commit -m "feat: add SQLAlchemy database models"
```

---

### Task 1.8: FastAPI应用入口

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/tests/test_api/test_main.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_main.py
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "NyxAI" in response.json()["name"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_main.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.storage.database import async_engine, Base
from app.utils.logger import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(level="DEBUG" if settings.DEBUG else "INFO")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Ops Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/api/__init__.py backend/tests/test_api/test_main.py
git commit -m "feat: add FastAPI application entry point"
```

---

### Task 1.9: Session API

**Files:**
- Create: `backend/app/api/sessions.py`
- Create: `backend/app/storage/repositories/session.py`
- Create: `backend/tests/test_api/test_sessions_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_sessions_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_session():
    response = client.post(
        "/api/v1/sessions",
        json={"trigger_type": "chat", "trigger_source": "user-input"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trigger_type"] == "chat"
    assert data["status"] == "investigating"


def test_list_sessions():
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_session():
    create_resp = client.post(
        "/api/v1/sessions",
        json={"trigger_type": "chat", "trigger_source": "test"},
    )
    session_id = create_resp.json()["id"]
    
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_sessions_api.py -v`
Expected: FAIL with "404" or "ModuleNotFoundError"

- [ ] **Step 3: Write repository implementation**

```python
# backend/app/storage/repositories/session.py
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.storage.models import SessionDB


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, trigger_type: str, trigger_source: str, status: SessionStatus = SessionStatus.INVESTIGATING
    ) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        db_session = SessionDB(
            id=session_id,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status.value,
        )
        self.session.add(db_session)
        await self.session.flush()
        
        return Session(
            id=session_id,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status,
            created_at=now,
            updated_at=now,
        )

    async def get(self, session_id: str) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        return Session(
            id=db_session.id,
            trigger_type=db_session.trigger_type,
            trigger_source=db_session.trigger_source,
            status=SessionStatus(db_session.status),
            investigation=db_session.investigation,
            root_cause=db_session.root_cause,
            recovery_plan=db_session.recovery_plan,
            execution_results=db_session.execution_results,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    async def list(self, limit: int = 50, offset: int = 0) -> List[Session]:
        result = await self.session.execute(
            select(SessionDB).order_by(SessionDB.created_at.desc()).limit(limit).offset(offset)
        )
        db_sessions = result.scalars().all()
        
        return [
            Session(
                id=s.id,
                trigger_type=s.trigger_type,
                trigger_source=s.trigger_source,
                status=SessionStatus(s.status),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in db_sessions
        ]

    async def update_status(self, session_id: str, status: SessionStatus) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.status = status.value
        await self.session.flush()
        
        return await self.get(session_id)
```

- [ ] **Step 4: Write API implementation**

```python
# backend/app/api/sessions.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.storage.database import get_async_session
from app.storage.repositories.session import SessionRepository

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    trigger_type: str
    trigger_source: str


@router.post("", response_model=Session)
async def create_session(
    request: CreateSessionRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    return await repo.create(request.trigger_type, request.trigger_source)


@router.get("", response_model=List[Session])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    return await repo.list(limit, offset)


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    session = await repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
```

- [ ] **Step 5: Register router in main.py**

```python
# Add to backend/app/main.py after health_check endpoint
from app.api.sessions import router as sessions_router
app.include_router(sessions_router)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_api/test_sessions_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/sessions.py backend/app/storage/repositories/session.py backend/app/main.py backend/tests/test_api/test_sessions_api.py
git commit -m "feat: add Session API with CRUD operations"
```

---

## Phase 2: Agent核心实现

### Task 2.1: Agent基类

**Files:**
- Create: `backend/app/agents/base.py`
- Create: `backend/tests/test_agents/test_base_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agents/test_base_agent.py
import pytest
from app.agents.base import BaseAgent, AgentContext, AgentResult


class TestAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(success=True, data={"message": "test"})


@pytest.mark.asyncio
async def test_base_agent_creation():
    agent = TestAgent(name="test_agent")
    assert agent.name == "test_agent"


@pytest.mark.asyncio
async def test_base_agent_execute():
    agent = TestAgent(name="test_agent")
    context = AgentContext(session_id="test-session")
    result = await agent.execute(context)
    assert result.success is True
    assert result.data["message"] == "test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_agents/test_base_agent.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    session_id: str
    query: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    evidence: List[Any] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_agents/test_base_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/base.py backend/tests/test_agents/test_base_agent.py
git commit -m "feat: add BaseAgent abstract class"
```

---

### Task 2.2: LLM服务

**Files:**
- Create: `backend/app/services/llm.py`
- Create: `backend/tests/test_services/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_services/test_llm.py
import pytest
from app.services.llm import LLMService, LLMConfig


def test_llm_config_creation():
    config = LLMConfig(provider="openai", model="gpt-4o")
    assert config.provider == "openai"
    assert config.model == "gpt-4o"


@pytest.mark.asyncio
async def test_llm_service_mock():
    service = LLMService(config=LLMConfig(provider="mock", model="mock"))
    response = await service.generate("test prompt")
    assert response is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_services/test_llm.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/llm.py
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import get_settings

settings = get_settings()


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]
    model: str


class LLMService:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        if self.config.provider == "mock":
            return LLMResponse(
                content="Mock response",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                model=self.config.model,
            )
        
        if self.config.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, history)
        
        raise ValueError(f"Unsupported provider: {self.config.provider}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[List[Dict[str, str]]],
    ) -> LLMResponse:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            model=response.model,
        )
```

- [ ] **Step 4: Create test directory and run test**

```bash
mkdir -p backend/tests/test_services
touch backend/tests/test_services/__init__.py
cd backend && uv run pytest tests/test_services/test_llm.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/llm.py backend/tests/test_services/
git commit -m "feat: add LLM service with multi-provider support"
```

---

### Task 2.3: 调查Agent

**Files:**
- Create: `backend/app/agents/investigation.py`
- Create: `backend/app/tools/__init__.py`
- Create: `backend/tests/test_agents/test_investigation.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agents/test_investigation.py
import pytest
from app.agents.base import AgentContext
from app.agents.investigation import InvestigationAgent


@pytest.mark.asyncio
async def test_investigation_agent_creation():
    agent = InvestigationAgent()
    assert agent.name == "investigation"


@pytest.mark.asyncio
async def test_investigation_agent_execute():
    agent = InvestigationAgent()
    context = AgentContext(
        session_id="test-session",
        query="数据库响应延迟超过5秒",
    )
    result = await agent.execute(context)
    assert result.success is True
    assert "anomalies" in result.data or "evidence" in result.data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_agents/test_investigation.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/agents/investigation.py
from datetime import datetime
from typing import List
import uuid

from app.agents.base import Agent, AgentContext, AgentResult
from app.models.evidence import Evidence, EvidenceType
from app.models.session import Anomaly
from app.services.llm import LLMService, LLMConfig


class InvestigationAgent(Agent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="investigation")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        
        system_prompt = """你是一个运维调查专家。你的任务是分析告警或问题描述，
识别可能的异常点，并收集相关证据。

请返回JSON格式的结果，包含：
1. anomalies: 识别的异常列表
2. evidence: 收集的证据列表
3. summary: 调查摘要"""
        
        response = await self.llm.generate(
            prompt=f"请调查以下问题：{query}",
            system_prompt=system_prompt,
        )
        
        evidence = [
            Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description=f"调查查询: {query}",
                source_data={"query": query},
                source_system="investigation_agent",
                timestamp=datetime.now(),
                confidence=0.8,
            )
        ]
        
        return AgentResult(
            success=True,
            data={
                "anomalies": [],
                "summary": response.content,
            },
            evidence=evidence,
        )

    async def load_knowledge(self, knowledge_types: List[str]) -> dict:
        knowledge = {}
        if "metric_definitions" in knowledge_types:
            knowledge["metric_definitions"] = "指标定义知识"
        if "log_patterns" in knowledge_types:
            knowledge["log_patterns"] = "日志模式知识"
        return knowledge
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_agents/test_investigation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/investigation.py backend/app/tools/__init__.py backend/tests/test_agents/test_investigation.py
git commit -m "feat: add InvestigationAgent"
```

---

### Task 2.4: 根因定界Agent

**Files:**
- Create: `backend/app/agents/diagnosis.py`
- Create: `backend/tests/test_agents/test_diagnosis.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agents/test_diagnosis.py
import pytest
from app.agents.base import AgentContext
from app.agents.diagnosis import DiagnosisAgent


@pytest.mark.asyncio
async def test_diagnosis_agent_creation():
    agent = DiagnosisAgent()
    assert agent.name == "diagnosis"


@pytest.mark.asyncio
async def test_diagnosis_agent_execute():
    agent = DiagnosisAgent()
    context = AgentContext(
        session_id="test-session",
        query="数据库延迟",
        metadata={"investigation_summary": "发现CPU使用率异常"},
    )
    result = await agent.execute(context)
    assert result.success is True
    assert "root_cause" in result.data
    assert "confidence" in result.data
    assert 0 <= result.data["confidence"] <= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_agents/test_diagnosis.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/agents/diagnosis.py
from datetime import datetime
from typing import List
import uuid

from app.agents.base import Agent, AgentContext, AgentResult
from app.models.evidence import Evidence, EvidenceNode, EvidenceType
from app.services.llm import LLMService, LLMConfig


class DiagnosisAgent(Agent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="diagnosis")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        investigation_summary = context.metadata.get("investigation_summary", "")
        
        system_prompt = """你是一个根因分析专家。你的任务是基于调查结果，
进行因果推理，确定根本原因，并生成证据链。

请返回JSON格式的结果，包含：
1. root_cause: 根因描述
2. confidence: 置信度(0-1)
3. evidence_chain: 证据链
4. affected_components: 受影响组件
5. reasoning_report: 推理报告"""
        
        prompt = f"""请分析以下问题的根因：
问题：{query}
调查摘要：{investigation_summary}"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        evidence_node = EvidenceNode(
            id=str(uuid.uuid4()),
            description="根因推理节点",
            evidence=Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description="推理证据",
                source_data={"reasoning": response.content},
                source_system="diagnosis_agent",
                timestamp=datetime.now(),
                confidence=0.85,
            ),
            inference_step="基于调查结果进行因果推理",
        )
        
        return AgentResult(
            success=True,
            data={
                "root_cause": response.content[:200] if response.content else "未知原因",
                "confidence": 0.85,
                "evidence_chain": [evidence_node.model_dump()],
                "affected_components": [],
                "reasoning_report": response.content,
            },
            evidence=[evidence_node.evidence],
        )

    async def load_knowledge(self, knowledge_types: List[str]) -> dict:
        knowledge = {}
        if "fault_patterns" in knowledge_types:
            knowledge["fault_patterns"] = "故障模式知识"
        if "causal_rules" in knowledge_types:
            knowledge["causal_rules"] = "因果推理规则"
        return knowledge
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_agents/test_diagnosis.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/diagnosis.py backend/tests/test_agents/test_diagnosis.py
git commit -m "feat: add DiagnosisAgent with evidence chain support"
```

---

### Task 2.5: 恢复Agent

**Files:**
- Create: `backend/app/agents/recovery.py`
- Create: `backend/tests/test_agents/test_recovery.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agents/test_recovery.py
import pytest
from app.agents.base import AgentContext
from app.agents.recovery import RecoveryAgent


@pytest.mark.asyncio
async def test_recovery_agent_creation():
    agent = RecoveryAgent()
    assert agent.name == "recovery"


@pytest.mark.asyncio
async def test_recovery_agent_execute():
    agent = RecoveryAgent()
    context = AgentContext(
        session_id="test-session",
        query="数据库延迟",
        metadata={
            "root_cause": "慢查询导致CPU过载",
            "confidence": 0.85,
        },
    )
    result = await agent.execute(context)
    assert result.success is True
    assert "actions" in result.data
    assert "risk_level" in result.data
    assert result.data["risk_level"] in ["low", "medium", "high"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_agents/test_recovery.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/agents/recovery.py
from typing import List

from app.agents.base import Agent, AgentContext, AgentResult
from app.models.session import RiskLevel
from app.services.llm import LLMService, LLMConfig


class RecoveryAgent(Agent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="recovery")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        root_cause = context.metadata.get("root_cause", "")
        confidence = context.metadata.get("confidence", 0.5)
        
        system_prompt = """你是一个故障恢复专家。你的任务是基于根因分析结果，
制定恢复方案，评估风险等级。

请返回JSON格式的结果，包含：
1. actions: 恢复操作列表
2. risk_level: 风险等级(low/medium/high)
3. requires_confirmation: 是否需要确认
4. rollback_plan: 回滚方案"""
        
        prompt = f"""请为以下问题制定恢复方案：
问题：{query}
根因：{root_cause}
置信度：{confidence}"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        risk_level = self._assess_risk(confidence)
        
        return AgentResult(
            success=True,
            data={
                "actions": [
                    {
                        "action_type": "investigate",
                        "description": "进一步调查确认",
                        "risk_level": "low",
                    }
                ],
                "risk_level": risk_level,
                "requires_confirmation": risk_level != "low",
                "rollback_plan": "暂无回滚方案",
                "estimated_impact": "低风险操作",
            },
        )

    def _assess_risk(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "low"
        elif confidence >= 0.5:
            return "medium"
        return "high"

    async def load_knowledge(self, knowledge_types: List[str]) -> dict:
        knowledge = {}
        if "recovery_playbooks" in knowledge_types:
            knowledge["recovery_playbooks"] = "恢复操作手册"
        if "safety_guidelines" in knowledge_types:
            knowledge["safety_guidelines"] = "安全操作规范"
        return knowledge
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_agents/test_recovery.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/recovery.py backend/tests/test_agents/test_recovery.py
git commit -m "feat: add RecoveryAgent with risk assessment"
```

---

### Task 2.6: Orchestrator Agent

**Files:**
- Create: `backend/app/agents/orchestrator.py`
- Create: `backend/tests/test_agents/test_orchestrator.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agents/test_orchestrator.py
import pytest
from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_orchestrator_creation():
    agent = OrchestratorAgent()
    assert agent.name == "orchestrator"


@pytest.mark.asyncio
async def test_orchestrator_execute():
    agent = OrchestratorAgent()
    context = AgentContext(
        session_id="test-session",
        query="数据库响应延迟超过5秒",
    )
    result = await agent.execute(context)
    assert result.success is True
    assert "status" in result.data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_agents/test_orchestrator.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/agents/orchestrator.py
from typing import Dict, Any

from app.agents.base import Agent, AgentContext, AgentResult
from app.agents.investigation import InvestigationAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.recovery import RecoveryAgent


class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__(name="orchestrator")
        self.investigation = InvestigationAgent()
        self.diagnosis = DiagnosisAgent()
        self.recovery = RecoveryAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        all_evidence = []
        
        inv_result = await self.investigation.execute(context)
        if not inv_result.success:
            return AgentResult(
                success=False,
                error="Investigation failed",
                data={"status": "failed", "stage": "investigation"},
            )
        all_evidence.extend(inv_result.evidence)
        
        diagnosis_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "investigation_summary": inv_result.data.get("summary", ""),
                "anomalies": inv_result.data.get("anomalies", []),
            },
        )
        diag_result = await self.diagnosis.execute(diagnosis_context)
        if not diag_result.success:
            return AgentResult(
                success=False,
                error="Diagnosis failed",
                data={"status": "failed", "stage": "diagnosis"},
            )
        all_evidence.extend(diag_result.evidence)
        
        recovery_context = AgentContext(
            session_id=context.session_id,
            query=context.query,
            metadata={
                "root_cause": diag_result.data.get("root_cause", ""),
                "confidence": diag_result.data.get("confidence", 0),
                "evidence_chain": diag_result.data.get("evidence_chain", []),
            },
        )
        rec_result = await self.recovery.execute(recovery_context)
        all_evidence.extend(rec_result.evidence)
        
        return AgentResult(
            success=True,
            data={
                "status": "completed",
                "investigation": inv_result.data,
                "diagnosis": diag_result.data,
                "recovery": rec_result.data,
            },
            evidence=all_evidence,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_agents/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/orchestrator.py backend/tests/test_agents/test_orchestrator.py
git commit -m "feat: add OrchestratorAgent for workflow coordination"
```

---

## Phase 3: Chat API

### Task 3.1: Chat API

**Files:**
- Create: `backend/app/api/chat.py`
- Create: `backend/tests/test_api/test_chat_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api/test_chat_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_message():
    response = client.post(
        "/api/v1/chat/message",
        json={"session_id": None, "message": "数据库响应延迟"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api/test_chat_api.py -v`
Expected: FAIL with "404"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/api/chat.py
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent
from app.storage.database import get_async_session
from app.storage.repositories.session import SessionRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    
    if not request.session_id:
        session = await repo.create(
            trigger_type="chat",
            trigger_source="user-input",
        )
        session_id = session.id
    else:
        session_id = request.session_id
        session = await repo.get(session_id)
        if not session:
            session = await repo.create(
                trigger_type="chat",
                trigger_source="user-input",
            )
            session_id = session.id
    
    orchestrator = OrchestratorAgent()
    context = AgentContext(
        session_id=session_id,
        query=request.message,
    )
    
    result = await orchestrator.execute(context)
    
    if result.success:
        recovery = result.data.get("recovery", {})
        response_text = recovery.get("actions", [{}])[0].get("description", "处理完成")
        if result.data.get("diagnosis", {}).get("root_cause"):
            response_text = f"根因分析: {result.data['diagnosis']['root_cause']}\n建议: {response_text}"
    else:
        response_text = f"处理失败: {result.error}"
    
    return ChatResponse(
        session_id=session_id,
        response=response_text,
        status=result.data.get("status", "unknown"),
    )
```

- [ ] **Step 4: Register router and run test**

```python
# Add to backend/app/main.py
from app.api.chat import router as chat_router
app.include_router(chat_router)
```

Run: `cd backend && uv run pytest tests/test_api/test_chat_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/chat.py backend/app/main.py backend/tests/test_api/test_chat_api.py
git commit -m "feat: add Chat API for conversational interaction"
```

---

## Phase 4: 前端基础

### Task 4.1: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: 初始化Vite项目**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

- [ ] **Step 2: 安装依赖**

```bash
cd frontend
npm install antd @ant-design/icons axios zustand react-router-dom
```

- [ ] **Step 3: 配置vite.config.ts**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 4: 创建基础App组件**

```tsx
// frontend/src/App.tsx
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div style={{ padding: 24 }}>
        <h1>NyxAI 运维智能体</h1>
        <p>系统初始化中...</p>
      </div>
    </ConfigProvider>
  )
}

export default App
```

- [ ] **Step 5: 验证前端启动**

```bash
cd frontend
npm run dev
```

Expected: 浏览器访问 http://localhost:3000 显示 "NyxAI 运维智能体"

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: initialize frontend with Vite + React + Ant Design"
```

---

### Task 4.2: API服务层

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建类型定义**

```typescript
// frontend/src/types/index.ts
export interface Session {
  id: string
  trigger_type: string
  trigger_source: string
  status: 'investigating' | 'diagnosing' | 'recovering' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface ChatRequest {
  session_id?: string
  message: string
}

export interface ChatResponse {
  session_id: string
  response: string
  status: string
}
```

- [ ] **Step 2: 创建API服务**

```typescript
// frontend/src/services/api.ts
import axios from 'axios'
import type { Session, ChatRequest, ChatResponse } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export const sessionsApi = {
  list: () => api.get<Session[]>('/sessions'),
  get: (id: string) => api.get<Session>(`/sessions/${id}`),
  create: (data: { trigger_type: string; trigger_source: string }) =>
    api.post<Session>('/sessions', data),
}

export const chatApi = {
  message: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/types/index.ts
git commit -m "feat: add frontend API service layer"
```

---

### Task 4.3: 对话界面组件

**Files:**
- Create: `frontend/src/components/Chat/ChatWindow.tsx`
- Create: `frontend/src/components/Chat/MessageInput.tsx`
- Create: `frontend/src/stores/sessionStore.ts`

- [ ] **Step 1: 创建状态管理**

```typescript
// frontend/src/stores/sessionStore.ts
import { create } from 'zustand'
import type { Session } from '../types'

interface SessionState {
  currentSession: Session | null
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  setCurrentSession: (session: Session | null) => void
  addMessage: (role: 'user' | 'assistant', content: string) => void
  clearMessages: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  currentSession: null,
  messages: [],
  setCurrentSession: (session) => set({ currentSession: session }),
  addMessage: (role, content) =>
    set((state) => ({ messages: [...state.messages, { role, content }] })),
  clearMessages: () => set({ messages: [] }),
}))
```

- [ ] **Step 2: 创建聊天窗口组件**

```tsx
// frontend/src/components/Chat/ChatWindow.tsx
import { List, Typography } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'

const { Text } = Typography

export function ChatWindow() {
  const messages = useSessionStore((state) => state.messages)

  return (
    <div style={{ height: 'calc(100vh - 200px)', overflow: 'auto', padding: 16 }}>
      <List
        dataSource={messages}
        renderItem={(item) => (
          <List.Item style={{ border: 'none' }}>
            <div style={{ display: 'flex', gap: 8, width: '100%' }}>
              {item.role === 'user' ? (
                <UserOutlined style={{ fontSize: 20 }} />
              ) : (
                <RobotOutlined style={{ fontSize: 20, color: '#1890ff' }} />
              )}
              <Text>{item.content}</Text>
            </div>
          </List.Item>
        )}
      />
    </div>
  )
}
```

- [ ] **Step 3: 创建消息输入组件**

```tsx
// frontend/src/components/Chat/MessageInput.tsx
import { Input, Button, Space } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { chatApi } from '../../services/api'
import { useSessionStore } from '../../stores/sessionStore'

const { TextArea } = Input

export function MessageInput() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const { currentSession, addMessage, setCurrentSession } = useSessionStore()

  const handleSend = async () => {
    if (!message.trim()) return

    addMessage('user', message)
    setLoading(true)

    try {
      const response = await chatApi.message({
        session_id: currentSession?.id,
        message,
      })
      
      addMessage('assistant', response.data.response)
      
      if (!currentSession) {
        setCurrentSession({
          id: response.data.session_id,
          trigger_type: 'chat',
          trigger_source: 'user-input',
          status: 'investigating',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      }
    } catch (error) {
      addMessage('assistant', '抱歉，发生了错误，请重试。')
    } finally {
      setLoading(false)
      setMessage('')
    }
  }

  return (
    <Space.Compact style={{ width: '100%' }}>
      <TextArea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="描述您的问题..."
        autoSize={{ minRows: 1, maxRows: 4 }}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault()
            handleSend()
          }
        }}
        style={{ flex: 1 }}
      />
      <Button type="primary" loading={loading} onClick={handleSend}>
        <SendOutlined />
      </Button>
    </Space.Compact>
  )
}
```

- [ ] **Step 4: 更新App.tsx**

```tsx
// frontend/src/App.tsx
import { ConfigProvider, Layout } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ChatWindow } from './components/Chat/ChatWindow'
import { MessageInput } from './components/Chat/MessageInput'

const { Content, Footer } = Layout

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: 24 }}>
          <ChatWindow />
        </Content>
        <Footer style={{ background: '#fff', padding: 16 }}>
          <MessageInput />
        </Footer>
      </Layout>
    </ConfigProvider>
  )
}

export default App
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ frontend/src/stores/ frontend/src/App.tsx
git commit -m "feat: add Chat UI components with state management"
```

---

## Phase 5: 集成与部署

### Task 5.1: Docker配置

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile.backend`
- Create: `Dockerfile.frontend`

- [ ] **Step 1: 创建后端Dockerfile**

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen --no-dev

COPY backend/app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建前端Dockerfile**

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

- [ ] **Step 3: 创建docker-compose.yml**

```yaml
# docker-compose.yml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/nyxai.db
      - DEBUG=true
    volumes:
      - ./data:/app/data
      - ./chroma_data:/app/chroma_data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml Dockerfile.backend Dockerfile.frontend
git commit -m "feat: add Docker configuration for deployment"
```

---

### Task 5.2: 最终集成测试

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_workflow():
    response = client.post(
        "/api/v1/chat/message",
        json={"message": "数据库响应延迟超过5秒，请帮我分析"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"]
    assert data["response"]
    
    session_id = data["session_id"]
    
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.status_code == 200
```

- [ ] **Step 2: Run integration test**

Run: `cd backend && uv run pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add integration test for full workflow"
```

---

## 总结

本实现计划包含以下阶段：

| Phase | 内容 | 任务数 |
|-------|------|--------|
| Phase 1 | 后端核心框架 | 9 |
| Phase 2 | Agent核心实现 | 6 |
| Phase 3 | Chat API | 1 |
| Phase 4 | 前端基础 | 3 |
| Phase 5 | 集成与部署 | 2 |

**总计**: 21个任务

每个任务遵循TDD原则：先写测试 → 运行失败 → 实现代码 → 测试通过 → 提交
