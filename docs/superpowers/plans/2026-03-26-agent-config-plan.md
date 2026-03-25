# Agent 在线配置系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent 在线配置系统，支持通过 Web UI 动态配置每个 Agent 的 system prompt 和可使用的 skill 列表。

**Architecture:** 采用独立配置表方案，新增 `agent_configs` 和 `agent_config_versions` 两张表存储配置和版本历史。后端提供 RESTful API，前端在设置页面新增配置管理模块。

**Tech Stack:** FastAPI, SQLAlchemy, React, TypeScript, Ant Design

---

## Task 1: 数据模型定义

**Files:**
- Create: `backend/app/models/agent_config.py`
- Modify: `backend/app/storage/models.py`
- Test: `backend/tests/test_models/test_agent_config.py`

- [ ] **Step 1: 创建 AgentConfig Pydantic 模型**

创建文件 `backend/app/models/agent_config.py`:

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentConfigBase(BaseModel):
    agent_type: str = Field(..., description="Agent类型")
    name: str = Field(..., description="配置名称")
    system_prompt: str = Field(..., description="系统提示词")
    allowed_skills: List[str] = Field(default_factory=list, description="可用技能列表")


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    allowed_skills: Optional[List[str]] = None
    change_reason: Optional[str] = None


class AgentConfig(AgentConfigBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentConfigVersionBase(BaseModel):
    version: int
    system_prompt: str
    allowed_skills: List[str]
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None


class AgentConfigVersion(AgentConfigVersionBase):
    id: str
    config_id: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 创建测试目录和测试文件**

创建目录 `backend/tests/test_models` 并创建 `__init__.py` 和 `test_agent_config.py`:

```python
import pytest
from app.models.agent_config import AgentConfig, AgentConfigCreate, AgentConfigUpdate


def test_agent_config_create():
    config = AgentConfigCreate(
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="你是一个诊断专家",
        allowed_skills=["brainstorming"]
    )
    assert config.agent_type == "diagnosis"
    assert config.name == "测试配置"
    assert config.system_prompt == "你是一个诊断专家"
    assert config.allowed_skills == ["brainstorming"]


def test_agent_config_update():
    update = AgentConfigUpdate(
        system_prompt="更新后的提示词",
        change_reason="优化诊断"
    )
    assert update.system_prompt == "更新后的提示词"
    assert update.change_reason == "优化诊断"
    assert update.name is None


def test_agent_config_allowed_skills_default():
    config = AgentConfigCreate(
        agent_type="investigation",
        name="默认配置",
        system_prompt="测试"
    )
    assert config.allowed_skills == []
```

- [ ] **Step 3: 运行测试验证模型定义**

Run: `cd backend; python -m pytest tests/test_models/test_agent_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 4: 添加 SQLAlchemy 数据库模型**

在 `backend/app/storage/models.py` 末尾添加:

```python
class AgentConfigDB(Base):
    __tablename__ = "agent_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(200))
    system_prompt: Mapped[str] = mapped_column(Text)
    allowed_skills: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class AgentConfigVersionDB(Base):
    __tablename__ = "agent_config_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    config_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_configs.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text)
    allowed_skills: Mapped[list] = mapped_column(JSON, default=list)
    changed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
```

- [ ] **Step 5: 验证数据库表自动创建**

项目使用 SQLAlchemy 的 `Base.metadata.create_all` 在启动时自动创建表。运行应用验证：

Run: `cd backend; python -c "from app.storage.database import Base; from app.storage.models import AgentConfigDB, AgentConfigVersionDB; print('Models loaded successfully')"`
Expected: 输出 "Models loaded successfully"

- [ ] **Step 6: 提交数据模型**

```bash
git add backend/app/models/agent_config.py backend/app/storage/models.py backend/tests/test_models/
git commit -m "feat: add AgentConfig and AgentConfigVersion data models"
```

---

## Task 2: 配置仓储实现

**Files:**
- Create: `backend/app/storage/repositories/agent_config_repo.py`
- Test: `backend/tests/test_storage/test_agent_config_repo.py`

- [ ] **Step 1: 创建 AgentConfigRepository**

创建文件 `backend/app/storage/repositories/agent_config_repo.py`:

```python
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigVersion
from app.storage.models import AgentConfigDB, AgentConfigVersionDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).order_by(AgentConfigDB.agent_type, AgentConfigDB.created_at.desc())
        )
        configs = result.scalars().all()
        return [self._to_model(c) for c in configs]

    async def get_by_type(self, agent_type: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(
                and_(AgentConfigDB.agent_type == agent_type, AgentConfigDB.is_active == True)
            )
        )
        config = result.scalar_one_or_none()
        return self._to_model(config) if config else None

    async def get_by_id(self, config_id: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        config = result.scalar_one_or_none()
        return self._to_model(config) if config else None

    async def create(self, data: AgentConfigCreate) -> AgentConfig:
        config_id = str(uuid.uuid4())
        now = datetime.now()
        
        db_config = AgentConfigDB(
            id=config_id,
            agent_type=data.agent_type,
            name=data.name,
            system_prompt=data.system_prompt,
            allowed_skills=data.allowed_skills,
            is_active=True,
        )
        self.session.add(db_config)
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Created config id={config_id} agent_type={data.agent_type}")
        return self._to_model(db_config)

    async def update(self, config_id: str, data: AgentConfigUpdate, changed_by: str = "system") -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        await self._create_version(db_config, changed_by, data.change_reason)
        
        if data.name is not None:
            db_config.name = data.name
        if data.system_prompt is not None:
            db_config.system_prompt = data.system_prompt
        if data.allowed_skills is not None:
            db_config.allowed_skills = data.allowed_skills
        
        db_config.updated_at = datetime.now()
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Updated config id={config_id}")
        return self._to_model(db_config)

    async def activate(self, config_id: str) -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        deactivate_result = await self.session.execute(
            select(AgentConfigDB).where(
                and_(AgentConfigDB.agent_type == db_config.agent_type, AgentConfigDB.is_active == True)
            )
        )
        for old_active in deactivate_result.scalars().all():
            old_active.is_active = False
        
        db_config.is_active = True
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Activated config id={config_id} agent_type={db_config.agent_type}")
        return self._to_model(db_config)

    async def delete(self, config_id: str) -> bool:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return False
        
        await self.session.delete(db_config)
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Deleted config id={config_id}")
        return True

    async def get_versions(self, config_id: str) -> List[AgentConfigVersion]:
        result = await self.session.execute(
            select(AgentConfigVersionDB)
            .where(AgentConfigVersionDB.config_id == config_id)
            .order_by(AgentConfigVersionDB.version.desc())
        )
        versions = result.scalars().all()
        return [self._to_version_model(v) for v in versions]

    async def rollback(self, config_id: str, version: int, changed_by: str = "system") -> Optional[AgentConfig]:
        result = await self.session.execute(
            select(AgentConfigDB).where(AgentConfigDB.id == config_id)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return None
        
        version_result = await self.session.execute(
            select(AgentConfigVersionDB).where(
                and_(AgentConfigVersionDB.config_id == config_id, AgentConfigVersionDB.version == version)
            )
        )
        db_version = version_result.scalar_one_or_none()
        if not db_version:
            return None
        
        await self._create_version(db_config, changed_by, f"回滚到版本 {version}")
        
        db_config.system_prompt = db_version.system_prompt
        db_config.allowed_skills = db_version.allowed_skills
        db_config.updated_at = datetime.now()
        await self.session.flush()
        
        logger.info(f"[AgentConfigRepository] Rolled back config id={config_id} to version {version}")
        return self._to_model(db_config)

    async def _create_version(self, db_config: AgentConfigDB, changed_by: str, change_reason: Optional[str]):
        version_result = await self.session.execute(
            select(AgentConfigVersionDB)
            .where(AgentConfigVersionDB.config_id == db_config.id)
            .order_by(AgentConfigVersionDB.version.desc())
            .limit(1)
        )
        last_version = version_result.scalar_one_or_none()
        next_version = (last_version.version + 1) if last_version else 1
        
        db_version = AgentConfigVersionDB(
            id=str(uuid.uuid4()),
            config_id=db_config.id,
            version=next_version,
            system_prompt=db_config.system_prompt,
            allowed_skills=db_config.allowed_skills,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        self.session.add(db_version)

    def _to_model(self, db_config: Optional[AgentConfigDB]) -> Optional[AgentConfig]:
        if not db_config:
            return None
        return AgentConfig(
            id=db_config.id,
            agent_type=db_config.agent_type,
            name=db_config.name,
            system_prompt=db_config.system_prompt,
            allowed_skills=db_config.allowed_skills or [],
            is_active=db_config.is_active,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
        )

    def _to_version_model(self, db_version: AgentConfigVersionDB) -> AgentConfigVersion:
        return AgentConfigVersion(
            id=db_version.id,
            config_id=db_version.config_id,
            version=db_version.version,
            system_prompt=db_version.system_prompt,
            allowed_skills=db_version.allowed_skills or [],
            changed_by=db_version.changed_by,
            change_reason=db_version.change_reason,
            created_at=db_version.created_at,
        )
```

- [ ] **Step 2: 创建仓储测试**

创建目录 `backend/tests/test_storage` 和文件 `test_agent_config_repo.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import AgentConfigCreate, AgentConfigUpdate
from app.storage.repositories.agent_config_repo import AgentConfigRepository


@pytest.mark.asyncio
async def test_create_config(db_session: AsyncSession):
    repo = AgentConfigRepository(db_session)
    config = await repo.create(AgentConfigCreate(
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="你是一个诊断专家",
        allowed_skills=["brainstorming"]
    ))
    
    assert config.id is not None
    assert config.agent_type == "diagnosis"
    assert config.is_active == True


@pytest.mark.asyncio
async def test_get_by_type(db_session: AsyncSession):
    repo = AgentConfigRepository(db_session)
    await repo.create(AgentConfigCreate(
        agent_type="investigation",
        name="调查配置",
        system_prompt="你是一个调查专家",
        allowed_skills=[]
    ))
    
    config = await repo.get_by_type("investigation")
    assert config is not None
    assert config.agent_type == "investigation"


@pytest.mark.asyncio
async def test_update_creates_version(db_session: AsyncSession):
    repo = AgentConfigRepository(db_session)
    created = await repo.create(AgentConfigCreate(
        agent_type="recovery",
        name="恢复配置",
        system_prompt="原始提示词",
        allowed_skills=[]
    ))
    
    updated = await repo.update(created.id, AgentConfigUpdate(
        system_prompt="更新后的提示词",
        change_reason="测试更新"
    ))
    
    assert updated.system_prompt == "更新后的提示词"
    
    versions = await repo.get_versions(created.id)
    assert len(versions) == 1
    assert versions[0].system_prompt == "原始提示词"
```

- [ ] **Step 3: 更新 conftest.py 添加 db_session fixture**

在 `backend/tests/conftest.py` 中添加:

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

- [ ] **Step 4: 运行仓储测试**

Run: `cd backend; python -m pytest tests/test_storage/test_agent_config_repo.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: 提交仓储代码**

```bash
git add backend/app/storage/repositories/agent_config_repo.py backend/tests/test_storage/ backend/tests/conftest.py
git commit -m "feat: add AgentConfigRepository with version support"
```

---

## Task 3: API 端点实现

**Files:**
- Create: `backend/app/api/agent_configs.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api/test_agent_configs.py`

- [ ] **Step 1: 创建 API 路由**

创建文件 `backend/app/api/agent_configs.py`:

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import (
    AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigVersion
)
from app.storage.database import get_session
from app.storage.repositories.agent_config_repo import AgentConfigRepository
from app.skills.registry import SkillRegistry
from app.config import get_settings
from pathlib import Path

router = APIRouter(prefix="/api/v1/agent-configs", tags=["agent-configs"])


def get_skill_registry() -> SkillRegistry:
    from app.main import app
    return app.state.skill_registry


@router.get("", response_model=List[AgentConfig])
async def list_configs(session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    return await repo.list_all()


@router.get("/{agent_type}", response_model=AgentConfig)
async def get_config_by_type(agent_type: str, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    config = await repo.get_by_type(agent_type)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config not found for agent_type: {agent_type}")
    return config


@router.post("", response_model=AgentConfig)
async def create_config(data: AgentConfigCreate, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    return await repo.create(data)


@router.put("/{config_id}", response_model=AgentConfig)
async def update_config(config_id: str, data: AgentConfigUpdate, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    config = await repo.update(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
    return config


@router.delete("/{config_id}")
async def delete_config(config_id: str, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    success = await repo.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
    return {"success": True}


@router.post("/{config_id}/activate", response_model=AgentConfig)
async def activate_config(config_id: str, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    config = await repo.activate(config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
    return config


@router.get("/{config_id}/versions", response_model=List[AgentConfigVersion])
async def list_versions(config_id: str, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    return await repo.get_versions(config_id)


@router.post("/{config_id}/rollback/{version}", response_model=AgentConfig)
async def rollback_config(config_id: str, version: int, session: AsyncSession = Depends(get_session)):
    repo = AgentConfigRepository(session)
    config = await repo.rollback(config_id, version)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config or version not found")
    return config


@router.get("/skills/list")
async def list_skills(skill_registry: SkillRegistry = Depends(get_skill_registry)):
    return skill_registry.list_metadata()
```

- [ ] **Step 2: 在 main.py 注册路由**

修改 `backend/app/main.py`，在导入区域添加（约第17行后）：

```python
from app.api.agent_configs import router as agent_configs_router
```

在路由注册区域添加（约第56行后，在其他 `app.include_router` 调用之后）：

```python
app.include_router(agent_configs_router)
```

完整修改后的 main.py 相关部分应如下：

```python
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.api.webhook import router as webhook_router
from app.api.websocket import router as websocket_router
from app.api.datasources import router as datasources_router
from app.api.agent_configs import router as agent_configs_router  # 新增

# ... 中间代码 ...

app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(webhook_router)
app.include_router(websocket_router)
app.include_router(datasources_router)
app.include_router(agent_configs_router)  # 新增
```

- [ ] **Step 3: 创建 API 测试**

创建文件 `backend/tests/test_api/test_agent_configs.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_configs_empty():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/agent-configs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_config():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/agent-configs", json={
            "agent_type": "diagnosis",
            "name": "测试诊断配置",
            "system_prompt": "你是一个诊断专家",
            "allowed_skills": ["brainstorming"]
        })
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["agent_type"] == "diagnosis"
    
    get_response = await client.get(f"/api/v1/agent-configs/diagnosis")
    assert get_response.status_code == 200
```

- [ ] **Step 4: 运行 API 测试**

Run: `cd backend; python -m pytest tests/test_api/test_agent_configs.py -v`
Expected: PASS

- [ ] **Step 5: 提交 API 代码**

```bash
git add backend/app/api/agent_configs.py backend/app/main.py backend/tests/test_api/test_agent_configs.py
git commit -m "feat: add agent config API endpoints"
```

---

## Task 4: BaseAgent 配置加载

**Files:**
- Modify: `backend/app/agents/base.py`
- Modify: `backend/app/agents/diagnosis.py`
- Modify: `backend/app/agents/investigation.py`
- Modify: `backend/app/agents/recovery.py`
- Test: `backend/tests/test_agents/test_config_loading.py`

- [ ] **Step 1: 修改 BaseAgent 添加配置加载**

修改 `backend/app/agents/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.skills.registry import SkillRegistry
from app.skills.types import Skill
from app.storage.repositories.agent_config_repo import AgentConfigRepository


@dataclass
class AgentContext:
    session_id: str
    query: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_skills: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    evidence: List[Any] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        skill_registry: Optional[SkillRegistry] = None,
        config_repo: Optional[AgentConfigRepository] = None,
    ):
        self.name = name
        self._skill_registry = skill_registry
        self._config_repo = config_repo
        self._config = None

    async def load_config(self) -> Optional[Dict[str, Any]]:
        if not self._config_repo:
            return None
        config = await self._config_repo.get_by_type(self.name)
        if config:
            self._config = config
        return config

    def get_system_prompt(self, default: str = "") -> str:
        if self._config:
            return self._config.system_prompt
        return default

    def get_allowed_skills(self, default: List[str] = None) -> List[str]:
        if self._config:
            return self._config.allowed_skills
        return default or []

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        return {}

    def build_skill_prompt(self, allowed_skills: List[str] = None) -> str:
        skills = allowed_skills or self.get_allowed_skills()
        if not self._skill_registry or not skills:
            return ""
        
        metadata_list = self._skill_registry.get_metadata(skills)
        if not metadata_list:
            return ""
        
        lines = ["## Available Skills", ""]
        lines.append("You have access to the following skills. Load a skill when its description matches your current task:")
        lines.append("")
        
        for metadata in metadata_list:
            lines.append(f"- **{metadata.name}**: {metadata.description}")
        
        lines.append("")
        lines.append("To use a skill, respond with: `LOAD_SKILL: <skill_name>`")
        
        return "\n".join(lines)

    def load_skill(self, name: str) -> Optional[Skill]:
        if not self._skill_registry:
            return None
        return self._skill_registry.load_skill(name)
```

- [ ] **Step 2: 修改 DiagnosisAgent 使用配置**

修改 `backend/app/agents/diagnosis.py` 的 execute 方法开头:

```python
async def execute(self, context: AgentContext) -> AgentResult:
    await self.load_config()
    
    default_prompt = """你是一个根因分析专家。你的任务是基于调查结果，
进行因果推理，确定根本原因，并生成证据链。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "root_cause": "根因描述",
    "confidence": 0.0-1.0,
    "affected_components": ["组件1", "组件2"],
    "reasoning_report": "详细推理报告",
    "evidence_chain": [{"description": "证据描述", "inference": "推理步骤"}]
}"""
    
    system_prompt = self.get_system_prompt(default_prompt)
```

- [ ] **Step 3: 修改 InvestigationAgent 使用配置**

修改 `backend/app/agents/investigation.py` 的 execute 方法开头:

```python
async def execute(self, context: AgentContext) -> AgentResult:
    await self.load_config()
    
    default_prompt = """你是一个运维调查专家。你的任务是分析告警或问题描述，
识别可能的异常点，并收集相关证据。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "anomalies": [{"name": "异常名称", "severity": "high/medium/low", "description": "描述"}],
    "evidence": [{"description": "证据描述", "source": "来源系统"}],
    "summary": "调查摘要",
    "confidence": 0.0-1.0
}"""
    
    system_prompt = self.get_system_prompt(default_prompt)
```

- [ ] **Step 4: 修改 RecoveryAgent 使用配置**

修改 `backend/app/agents/recovery.py` 的 execute 方法开头:

```python
async def execute(self, context: AgentContext) -> AgentResult:
    await self.load_config()
    
    default_prompt = """你是一个故障恢复专家。你的任务是基于根因分析结果，
制定恢复方案，评估风险等级。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "actions": [
        {
            "action_type": "restart/scale/configure/investigate",
            "description": "操作描述",
            "risk_level": "low/medium/high",
            "target": "目标组件"
        }
    ],
    "risk_level": "low/medium/high",
    "requires_confirmation": true/false,
    "rollback_plan": "回滚方案描述",
    "estimated_impact": "影响评估"
}"""
    
    system_prompt = self.get_system_prompt(default_prompt)
```

- [ ] **Step 5: 创建配置加载测试**

创建文件 `backend/tests/test_agents/test_config_loading.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.diagnosis import DiagnosisAgent
from app.models.agent_config import AgentConfig


@pytest.mark.asyncio
async def test_agent_uses_config_prompt():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=AgentConfig(
        id="test-id",
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="自定义诊断提示词",
        allowed_skills=["brainstorming"],
        is_active=True,
        created_at=None,
        updated_at=None,
    ))
    
    agent = DiagnosisAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "自定义诊断提示词"


@pytest.mark.asyncio
async def test_agent_uses_default_when_no_config():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=None)
    
    agent = DiagnosisAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "默认提示词"
```

- [ ] **Step 6: 运行测试**

Run: `cd backend; python -m pytest tests/test_agents/test_config_loading.py -v`
Expected: PASS

- [ ] **Step 7: 提交配置加载代码**

```bash
git add backend/app/agents/ backend/tests/test_agents/test_config_loading.py
git commit -m "feat: integrate config loading into BaseAgent"
```

---

## Task 5: 前端类型定义和 API 服务

**Files:**
- Create: `frontend/src/types/agentConfig.ts`
- Create: `frontend/src/services/agentConfigApi.ts`

- [ ] **Step 1: 创建类型定义**

创建文件 `frontend/src/types/agentConfig.ts`:

```typescript
export interface AgentConfig {
  id: string
  agent_type: string
  name: string
  system_prompt: string
  allowed_skills: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AgentConfigCreate {
  agent_type: string
  name: string
  system_prompt: string
  allowed_skills?: string[]
}

export interface AgentConfigUpdate {
  name?: string
  system_prompt?: string
  allowed_skills?: string[]
  change_reason?: string
}

export interface AgentConfigVersion {
  id: string
  config_id: string
  version: number
  system_prompt: string
  allowed_skills: string[]
  changed_by: string | null
  change_reason: string | null
  created_at: string
}

export interface SkillMetadata {
  name: string
  description: string
  path: string
}
```

- [ ] **Step 2: 创建 API 服务**

创建文件 `frontend/src/services/agentConfigApi.ts`:

```typescript
import api from './api'
import type { AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigVersion, SkillMetadata } from '../types/agentConfig'

export const agentConfigApi = {
  list: () =>
    api.get<AgentConfig[]>('/agent-configs').then(res => res.data),

  getByType: (agentType: string) =>
    api.get<AgentConfig>(`/agent-configs/${agentType}`).then(res => res.data),

  create: (data: AgentConfigCreate) =>
    api.post<AgentConfig>('/agent-configs', data).then(res => res.data),

  update: (id: string, data: AgentConfigUpdate) =>
    api.put<AgentConfig>(`/agent-configs/${id}`, data).then(res => res.data),

  delete: (id: string) =>
    api.delete(`/agent-configs/${id}`).then(res => res.data),

  activate: (id: string) =>
    api.post<AgentConfig>(`/agent-configs/${id}/activate`).then(res => res.data),

  getVersions: (id: string) =>
    api.get<AgentConfigVersion[]>(`/agent-configs/${id}/versions`).then(res => res.data),

  rollback: (id: string, version: number) =>
    api.post<AgentConfig>(`/agent-configs/${id}/rollback/${version}`).then(res => res.data),

  listSkills: () =>
    api.get<SkillMetadata[]>('/agent-configs/skills/list').then(res => res.data),
}
```

- [ ] **Step 3: 提交前端类型和 API**

```bash
git add frontend/src/types/agentConfig.ts frontend/src/services/agentConfigApi.ts
git commit -m "feat: add frontend types and API for agent config"
```

---

## Task 6: 前端配置管理页面

**Files:**
- Create: `frontend/src/components/AgentConfig/ConfigEditor.tsx`
- Create: `frontend/src/components/AgentConfig/SkillSelector.tsx`
- Create: `frontend/src/components/AgentConfig/VersionHistory.tsx`
- Modify: `frontend/src/components/Settings/SettingsSidebar.tsx`
- Modify: `frontend/src/stores/settingsStore.ts`

- [ ] **Step 1: 创建技能选择器组件**

创建文件 `frontend/src/components/AgentConfig/SkillSelector.tsx`:

```tsx
import React, { useEffect, useState } from 'react'
import { Checkbox, Spin, message } from 'antd'
import type { SkillMetadata } from '../../types/agentConfig'
import { agentConfigApi } from '../../services/agentConfigApi'

interface SkillSelectorProps {
  value: string[]
  onChange: (skills: string[]) => void
}

const SkillSelector: React.FC<SkillSelectorProps> = ({ value, onChange }) => {
  const [skills, setSkills] = useState<SkillMetadata[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    agentConfigApi.listSkills()
      .then(setSkills)
      .catch(() => message.error('加载技能列表失败'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <Spin />
  }

  return (
    <Checkbox.Group
      value={value}
      onChange={onChange}
      style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
    >
      {skills.map(skill => (
        <Checkbox key={skill.name} value={skill.name}>
          <strong>{skill.name}</strong>
          <span style={{ color: '#666', marginLeft: '8px' }}>{skill.description}</span>
        </Checkbox>
      ))}
    </Checkbox.Group>
  )
}

export default SkillSelector
```

- [ ] **Step 2: 创建版本历史组件**

创建文件 `frontend/src/components/AgentConfig/VersionHistory.tsx`:

```tsx
import React from 'react'
import { Timeline, Typography, Empty } from 'antd'
import type { AgentConfigVersion } from '../../types/agentConfig'

const { Text } = Typography

interface VersionHistoryProps {
  versions: AgentConfigVersion[]
  onRollback: (version: number) => void
}

const VersionHistory: React.FC<VersionHistoryProps> = ({ versions, onRollback }) => {
  if (versions.length === 0) {
    return <Empty description="暂无版本历史" />
  }

  return (
    <Timeline
      items={versions.map(v => ({
        color: 'blue',
        children: (
          <div>
            <Text strong>版本 {v.version}</Text>
            <br />
            <Text type="secondary">{v.change_reason || '无变更说明'}</Text>
            <br />
            <Text type="secondary">{new Date(v.created_at).toLocaleString()}</Text>
          </div>
        ),
      }))}
    />
  )
}

export default VersionHistory
```

- [ ] **Step 3: 创建配置编辑器组件**

创建文件 `frontend/src/components/AgentConfig/ConfigEditor.tsx`:

```tsx
import React, { useEffect, useState } from 'react'
import { Form, Input, Select, Button, message, Spin, Card } from 'antd'
import type { AgentConfig, AgentConfigCreate, AgentConfigUpdate } from '../../types/agentConfig'
import { agentConfigApi } from '../../services/agentConfigApi'
import SkillSelector from './SkillSelector'

const { TextArea } = Input
const { Option } = Select

const AGENT_TYPES = [
  { value: 'investigation', label: '调查 Agent' },
  { value: 'diagnosis', label: '诊断 Agent' },
  { value: 'recovery', label: '恢复 Agent' },
  { value: 'orchestrator', label: '编排 Agent' },
]

interface ConfigEditorProps {
  config?: AgentConfig
  onSave: () => void
  onCancel: () => void
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ config, onSave, onCancel }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config)
    }
  }, [config, form])

  const handleSubmit = async (values: AgentConfigCreate | AgentConfigUpdate) => {
    setLoading(true)
    try {
      if (config) {
        await agentConfigApi.update(config.id, values)
        message.success('配置已更新')
      } else {
        await agentConfigApi.create(values as AgentConfigCreate)
        message.success('配置已创建')
      }
      onSave()
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title={config ? '编辑配置' : '新建配置'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ allowed_skills: [] }}
      >
        <Form.Item
          name="agent_type"
          label="Agent 类型"
          rules={[{ required: true, message: '请选择 Agent 类型' }]}
        >
          <Select disabled={!!config}>
            {AGENT_TYPES.map(t => (
              <Option key={t.value} value={t.value}>{t.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="name"
          label="配置名称"
          rules={[{ required: true, message: '请输入配置名称' }]}
        >
          <Input placeholder="如：默认诊断配置" />
        </Form.Item>

        <Form.Item
          name="system_prompt"
          label="系统提示词"
          rules={[{ required: true, message: '请输入系统提示词' }]}
        >
          <TextArea rows={10} placeholder="输入 Agent 的系统提示词..." />
        </Form.Item>

        <Form.Item
          name="allowed_skills"
          label="可用技能"
        >
          <SkillSelector />
        </Form.Item>

        <Form.Item
          name="change_reason"
          label="变更说明"
        >
          <Input placeholder="描述本次变更的原因（可选）" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={onCancel}>
            取消
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default ConfigEditor
```

- [ ] **Step 4: 更新 SettingsSidebar 添加配置入口**

修改 `frontend/src/components/Settings/SettingsSidebar.tsx`:

```tsx
import React from 'react'
import { DatabaseOutlined, BookOutlined, SettingOutlined } from '@ant-design/icons'
import { useSettingsStore } from '../../stores/settingsStore'

const SettingsSidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useSettingsStore()

  const tabs = [
    { key: 'datasource', label: '数据源', icon: <DatabaseOutlined /> },
    { key: 'knowledge', label: '知识', icon: <BookOutlined /> },
    { key: 'agentConfig', label: 'Agent配置', icon: <SettingOutlined /> },
  ]

  return (
    <div className="settings-sidebar">
      {tabs.map((tab) => (
        <div
          key={tab.key}
          className={`settings-tab ${activeTab === tab.key ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.key as 'datasource' | 'knowledge' | 'agentConfig')}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </div>
      ))}
    </div>
  )
}

export default SettingsSidebar
```

- [ ] **Step 5: 更新 settingsStore 添加 agentConfig tab**

修改 `frontend/src/stores/settingsStore.ts`:

```typescript
interface SettingsState {
  isOpen: boolean
  activeTab: 'datasource' | 'knowledge' | 'agentConfig'
  setActiveTab: (tab: 'datasource' | 'knowledge' | 'agentConfig') => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isOpen: false,
  activeTab: 'datasource',
  setActiveTab: (tab) => set({ activeTab: tab }),
}))
```

- [ ] **Step 6: 更新 SettingsPage 添加配置管理内容**

修改 `frontend/src/components/Settings/SettingsPage.tsx`，添加 agentConfig 内容区域。

首先导入新组件：

```tsx
import ConfigEditor from '../AgentConfig/ConfigEditor'
import { agentConfigApi } from '../../services/agentConfigApi'
import type { AgentConfig } from '../../types/agentConfig'
```

在组件内添加状态：

```tsx
const [configs, setConfigs] = useState<AgentConfig[]>([])
const [editingConfig, setEditingConfig] = useState<AgentConfig | undefined>()
const [showEditor, setShowEditor] = useState(false)
```

添加加载配置的 useEffect：

```tsx
useEffect(() => {
  if (activeTab === 'agentConfig') {
    agentConfigApi.list().then(setConfigs)
  }
}, [activeTab])
```

在渲染内容区域添加 agentConfig 分支：

```tsx
{activeTab === 'agentConfig' && (
  <div className="settings-content">
    <Button type="primary" onClick={() => { setEditingConfig(undefined); setShowEditor(true) }}>
      新建配置
    </Button>
    <List
      dataSource={configs}
      renderItem={item => (
        <List.Item
          actions={[
            <Button type="link" onClick={() => { setEditingConfig(item); setShowEditor(true) }}>编辑</Button>,
            <Button type="link" danger onClick={() => agentConfigApi.delete(item.id).then(() => agentConfigApi.list().then(setConfigs))}>删除</Button>,
          ]}
        >
          <List.Item.Meta
            title={`${item.name} ${item.is_active ? '(激活)' : ''}`}
            description={`类型: ${item.agent_type} | 技能: ${item.allowed_skills.join(', ') || '无'}`}
          />
        </List.Item>
      )}
    />
    {showEditor && (
      <SlidePanel open={showEditor} onClose={() => setShowEditor(false)}>
        <ConfigEditor
          config={editingConfig}
          onSave={() => { setShowEditor(false); agentConfigApi.list().then(setConfigs); }}
          onCancel={() => setShowEditor(false)}
        />
      </SlidePanel>
    )}
  </div>
)}
```

- [ ] **Step 7: 提交前端配置管理页面**

```bash
git add frontend/src/components/AgentConfig/ frontend/src/components/Settings/ frontend/src/stores/settingsStore.ts
git commit -m "feat: add agent config management UI"
```

---

## Task 7: 集成测试和文档

**Files:**
- Create: `backend/tests/test_integration/test_agent_config_flow.py`

- [ ] **Step 1: 创建集成测试**

创建文件 `backend/tests/test_integration/test_agent_config_flow.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import AgentConfigCreate, AgentConfigUpdate
from app.storage.repositories.agent_config_repo import AgentConfigRepository
from app.agents.diagnosis import DiagnosisAgent


@pytest.mark.asyncio
async def test_full_config_flow(db_session: AsyncSession):
    repo = AgentConfigRepository(db_session)
    
    config = await repo.create(AgentConfigCreate(
        agent_type="diagnosis",
        name="集成测试配置",
        system_prompt="集成测试提示词",
        allowed_skills=["brainstorming"]
    ))
    assert config.id is not None
    
    updated = await repo.update(config.id, AgentConfigUpdate(
        system_prompt="更新后的提示词",
        change_reason="集成测试更新"
    ))
    assert updated.system_prompt == "更新后的提示词"
    
    versions = await repo.get_versions(config.id)
    assert len(versions) == 1
    
    agent = DiagnosisAgent(config_repo=repo)
    await agent.load_config()
    assert agent.get_system_prompt("默认") == "更新后的提示词"
```

- [ ] **Step 2: 运行所有测试**

Run: `cd backend; python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 3: 提交集成测试**

```bash
git add backend/tests/test_integration/
git commit -m "test: add integration test for agent config flow"
```

---

## Task 8: 最终验证

- [ ] **Step 1: 运行后端完整测试套件**

Run: `cd backend; python -m pytest -v --cov=app`
Expected: All tests PASS, coverage report generated

- [ ] **Step 2: 运行前端类型检查**

Run: `cd frontend; npm run typecheck`
Expected: No errors

- [ ] **Step 3: 启动开发服务器验证功能**

Run: `cd backend; uvicorn app.main:app --reload`
Verify: API endpoints accessible at http://localhost:8000/docs

- [ ] **Step 4: 提交最终代码**

```bash
git add -A
git commit -m "feat: complete agent config system implementation"
```
