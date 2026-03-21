# Agent对话系统增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现Agent对话系统增强功能，包括实时展示Agent思考过程、会话管理、数据源管理和知识管理。

**Architecture:** WebSocket替代SSE实现双向实时通信，前端使用Zustand管理状态，后端使用FastAPI WebSocket处理连接，数据存储在SQLite/PostgreSQL，向量知识存储在Chroma。

**Tech Stack:** React + TypeScript + Vite + Ant Design + Zustand (前端) | FastAPI + SQLAlchemy + WebSocket (后端) | Chroma (向量存储)

---

## 文件结构

### 后端文件

| 文件路径 | 职责 |
|---------|------|
| `backend/app/api/websocket.py` | WebSocket连接管理和消息处理 |
| `backend/app/api/datasources.py` | 数据源管理API |
| `backend/app/models/datasource.py` | 数据源Pydantic模型 |
| `backend/app/models/agent.py` | Agent执行Pydantic模型 |
| `backend/app/models/knowledge.py` | 知识Pydantic模型 |
| `backend/app/services/connection_tester.py` | 连接测试服务 |
| `backend/app/services/document_parser.py` | 文档解析服务 |
| `backend/app/storage/repositories/datasource_repo.py` | 数据源数据仓库 |
| `backend/app/storage/repositories/agent_exec_repo.py` | Agent执行数据仓库 |

### 后端修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `backend/app/storage/models.py` | 添加DataSourceDB、KnowledgeDB、AgentExecutionDB模型 |
| `backend/app/agents/base.py` | 添加AgentIdentity类 |
| `backend/app/agents/orchestrator.py` | 支持流式输出Agent事件 |
| `backend/app/api/knowledge.py` | 扩展知识管理API |
| `backend/app/main.py` | 注册WebSocket路由 |

### 前端文件

| 文件路径 | 职责 |
|---------|------|
| `frontend/src/types/agent.ts` | Agent相关类型定义 |
| `frontend/src/types/datasource.ts` | 数据源类型定义 |
| `frontend/src/types/knowledge.ts` | 知识类型定义 |
| `frontend/src/services/websocket.ts` | WebSocket服务 |
| `frontend/src/services/datasourceApi.ts` | 数据源API服务 |
| `frontend/src/services/knowledgeApi.ts` | 知识API服务 |
| `frontend/src/stores/agentStore.ts` | Agent状态管理 |
| `frontend/src/stores/settingsStore.ts` | 设置状态管理 |
| `frontend/src/components/Agent/AgentProcessPanel.tsx` | Agent思考过程面板 |
| `frontend/src/components/Agent/AgentCard.tsx` | Agent卡片组件 |
| `frontend/src/components/Agent/ThinkingStream.tsx` | 思考过程流式展示 |
| `frontend/src/components/Agent/ToolCallItem.tsx` | 工具调用项组件 |
| `frontend/src/components/Agent/HandoffIndicator.tsx` | Agent交接指示器 |
| `frontend/src/components/Timeline/VerticalTimeline.tsx` | 竖排时间线 |
| `frontend/src/components/Timeline/TimelineNode.tsx` | 时间线节点 |
| `frontend/src/components/Session/SessionSidebar.tsx` | 会话侧边栏 |
| `frontend/src/components/Session/SessionList.tsx` | 会话列表 |
| `frontend/src/components/Session/SessionToolbar.tsx` | 会话工具栏 |
| `frontend/src/components/Settings/SettingsPage.tsx` | 设置页面 |
| `frontend/src/components/Settings/SettingsSidebar.tsx` | 设置侧边Tab |
| `frontend/src/components/Settings/DataSourceList.tsx` | 数据源列表 |
| `frontend/src/components/Settings/DataSourceForm.tsx` | 数据源表单 |
| `frontend/src/components/Settings/KnowledgeList.tsx` | 知识列表 |
| `frontend/src/components/Settings/KnowledgeForm.tsx` | 知识表单 |
| `frontend/src/components/Settings/SlidePanel.tsx` | 侧滑面板 |

### 前端修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `frontend/src/stores/sessionStore.ts` | 扩展会话管理功能 |
| `frontend/src/components/Chat/ChatWindow.tsx` | 集成WebSocket和Agent组件 |
| `frontend/src/App.tsx` | 添加设置页面入口 |

---

## Task 1: 后端数据模型

**Files:**
- Modify: `backend/app/storage/models.py`

- [ ] **Step 1: 添加DataSourceDB模型**

在 `backend/app/storage/models.py` 中添加：

```python
class DataSourceDB(Base):
    __tablename__ = "datasources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    auth_type = Column(String, default="none")
    auth_config = Column(JSON, nullable=True)
    status = Column(String, default="not_configured")
    last_check = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 添加KnowledgeDB模型**

在 `backend/app/storage/models.py` 中添加：

```python
class KnowledgeDB(Base):
    __tablename__ = "knowledge"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String, default="text")
    file_url = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    category = Column(String, nullable=True)
    reference_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 3: 添加AgentExecutionDB模型**

在 `backend/app/storage/models.py` 中添加：

```python
class AgentExecutionDB(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    agent_display_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    status = Column(String, default="running")
    thoughts = Column(JSON, default=list)
    tool_calls = Column(JSON, default=list)
    result = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
```

- [ ] **Step 4: 运行数据库迁移**

```bash
cd backend
alembic revision --autogenerate -m "add datasource knowledge agent_execution tables"
alembic upgrade head
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/storage/models.py
git commit -m "feat(db): add DataSourceDB, KnowledgeDB, AgentExecutionDB models"
```

---

## Task 2: 后端Pydantic模型

**Files:**
- Create: `backend/app/models/datasource.py`
- Create: `backend/app/models/agent.py`
- Create: `backend/app/models/knowledge.py`

- [ ] **Step 1: 创建数据源模型**

创建 `backend/app/models/datasource.py`：

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class DataSourceBase(BaseModel):
    type: Literal["prometheus", "influxdb", "loki", "jaeger"]
    name: str
    url: str
    auth_type: Literal["none", "basic", "bearer", "api_key"] = "none"
    auth_config: Optional[dict] = None

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None

class DataSource(DataSourceBase):
    id: str
    status: str
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DataSourceTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None
```

- [ ] **Step 2: 创建Agent模型**

创建 `backend/app/models/agent.py`：

```python
from pydantic import BaseModel
from typing import Optional, Literal, List, Any
from datetime import datetime

class AgentIdentity(BaseModel):
    id: str
    name: str
    display_name: str
    type: Literal["investigation", "diagnosis", "recovery", "orchestrator"]
    icon: Optional[str] = None

class ToolCallRecord(BaseModel):
    tool: str
    params: dict
    result: Optional[Any] = None
    status: Literal["pending", "running", "success", "error"] = "pending"
    timestamp: str

class AgentExecutionBase(BaseModel):
    session_id: str
    agent: AgentIdentity
    status: Literal["idle", "running", "completed", "failed"] = "running"

class AgentExecutionCreate(AgentExecutionBase):
    pass

class AgentExecution(AgentExecutionBase):
    id: str
    thoughts: List[str] = []
    tool_calls: List[ToolCallRecord] = []
    result: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    class Config:
        from_attributes = True

class ServerMessage(BaseModel):
    type: str
    agent: Optional[AgentIdentity] = None
    payload: Any
    timestamp: str
    sequence: int
```

- [ ] **Step 3: 创建知识模型**

创建 `backend/app/models/knowledge.py`：

```python
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

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
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/datasource.py backend/app/models/agent.py backend/app/models/knowledge.py
git commit -m "feat(models): add Pydantic models for datasource, agent, knowledge"
```

---

## Task 3: 后端数据仓库

**Files:**
- Create: `backend/app/storage/repositories/datasource_repo.py`
- Create: `backend/app/storage/repositories/agent_exec_repo.py`

- [ ] **Step 1: 创建数据源仓库**

创建 `backend/app/storage/repositories/datasource_repo.py`：

```python
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.storage.models import DataSourceDB
from backend.app.models.datasource import DataSourceCreate, DataSourceUpdate

class DataSourceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[DataSourceDB]:
        return self.db.query(DataSourceDB).all()
    
    def get_by_id(self, ds_id: str) -> Optional[DataSourceDB]:
        return self.db.query(DataSourceDB).filter(DataSourceDB.id == ds_id).first()
    
    def get_by_type(self, ds_type: str) -> List[DataSourceDB]:
        return self.db.query(DataSourceDB).filter(DataSourceDB.type == ds_type).all()
    
    def create(self, data: DataSourceCreate) -> DataSourceDB:
        db_obj = DataSourceDB(**data.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, ds_id: str, data: DataSourceUpdate) -> Optional[DataSourceDB]:
        db_obj = self.get_by_id(ds_id)
        if db_obj:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def update_status(self, ds_id: str, status: str, error_message: Optional[str] = None) -> Optional[DataSourceDB]:
        db_obj = self.get_by_id(ds_id)
        if db_obj:
            db_obj.status = status
            db_obj.error_message = error_message
            db_obj.last_check = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, ds_id: str) -> bool:
        db_obj = self.get_by_id(ds_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
```

- [ ] **Step 2: 创建Agent执行仓库**

创建 `backend/app/storage/repositories/agent_exec_repo.py`：

```python
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.storage.models import AgentExecutionDB
from backend.app.models.agent import AgentExecutionCreate

class AgentExecutionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_session(self, session_id: str) -> List[AgentExecutionDB]:
        return self.db.query(AgentExecutionDB).filter(
            AgentExecutionDB.session_id == session_id
        ).order_by(AgentExecutionDB.started_at).all()
    
    def get_by_id(self, exec_id: str) -> Optional[AgentExecutionDB]:
        return self.db.query(AgentExecutionDB).filter(AgentExecutionDB.id == exec_id).first()
    
    def create(self, data: AgentExecutionCreate) -> AgentExecutionDB:
        db_obj = AgentExecutionDB(
            session_id=data.session_id,
            agent_name=data.agent.name,
            agent_display_name=data.agent.display_name,
            agent_type=data.agent.type,
            status=data.status
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def add_thought(self, exec_id: str, thought: str) -> Optional[AgentExecutionDB]:
        db_obj = self.get_by_id(exec_id)
        if db_obj:
            thoughts = db_obj.thoughts or []
            thoughts.append(thought)
            db_obj.thoughts = thoughts
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def add_tool_call(self, exec_id: str, tool_call: dict) -> Optional[AgentExecutionDB]:
        db_obj = self.get_by_id(exec_id)
        if db_obj:
            tool_calls = db_obj.tool_calls or []
            tool_calls.append(tool_call)
            db_obj.tool_calls = tool_calls
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def complete(self, exec_id: str, result: str, status: str = "completed") -> Optional[AgentExecutionDB]:
        db_obj = self.get_by_id(exec_id)
        if db_obj:
            db_obj.result = result
            db_obj.status = status
            db_obj.completed_at = datetime.utcnow()
            db_obj.duration_ms = int((db_obj.completed_at - db_obj.started_at).total_seconds() * 1000)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/storage/repositories/datasource_repo.py backend/app/storage/repositories/agent_exec_repo.py
git commit -m "feat(repo): add DataSourceRepository and AgentExecutionRepository"
```

---

## Task 4: 后端WebSocket实现

**Files:**
- Create: `backend/app/api/websocket.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/agents/orchestrator.py`

- [ ] **Step 1: 为OrchestratorAgent添加run_stream方法**

在 `backend/app/agents/orchestrator.py` 中添加流式输出支持（在现有 `execute` 方法后添加）：

```python
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import uuid

async def run_stream(self, session_id: str, content: str) -> AsyncGenerator[Dict[str, Any], None]:
    agent_identity = {
        "id": str(uuid.uuid4()),
        "name": "OrchestratorAgent",
        "display_name": "编排Agent",
        "type": "orchestrator"
    }
    
    yield {
        "type": "orchestrator_status",
        "payload": {"status": "started", "plan": ["InvestigationAgent", "DiagnosisAgent", "RecoveryAgent"]},
        "agent": agent_identity
    }
    
    context = AgentContext(session_id=session_id, query=content, metadata={})
    
    investigation_identity = {
        "id": f"investigation_{uuid.uuid4().hex[:8]}",
        "name": "InvestigationAgent",
        "display_name": "调查Agent",
        "type": "investigation",
        "icon": "search"
    }
    
    yield {
        "type": "agent_start",
        "agent": investigation_identity,
        "payload": {"description": "开始调查异常..."}
    }
    
    yield {
        "type": "agent_thinking",
        "agent": investigation_identity,
        "payload": {"thought": f"分析用户输入: {content}"}
    }
    
    inv_result = await self.investigation.execute(context)
    
    if inv_result.evidence:
        for i, ev in enumerate(inv_result.evidence):
            yield {
                "type": "tool_call",
                "agent": investigation_identity,
                "payload": {"tool": ev.source_system, "params": {}}
            }
            yield {
                "type": "tool_result",
                "agent": investigation_identity,
                "payload": {"tool": ev.source_system, "result": ev.source_data}
            }
    
    yield {
        "type": "agent_complete",
        "agent": investigation_identity,
        "payload": {"summary": inv_result.data.get("summary", "调查完成")}
    }
    
    if not inv_result.success:
        yield {
            "type": "error",
            "payload": {"message": "Investigation failed", "stage": "investigation"}
        }
        return
    
    diagnosis_identity = {
        "id": f"diagnosis_{uuid.uuid4().hex[:8]}",
        "name": "DiagnosisAgent",
        "display_name": "诊断Agent",
        "type": "diagnosis",
        "icon": "diagnosis"
    }
    
    yield {
        "type": "handoff",
        "agent": investigation_identity,
        "payload": {"to_agent": diagnosis_identity, "context": "调查完成，进入根因分析阶段"}
    }
    
    yield {
        "type": "agent_start",
        "agent": diagnosis_identity,
        "payload": {"description": "开始根因分析..."}
    }
    
    diagnosis_context = AgentContext(
        session_id=context.session_id,
        query=context.query,
        metadata={
            "investigation_summary": inv_result.data.get("summary", ""),
            "anomalies": inv_result.data.get("anomalies", []),
        }
    )
    diag_result = await self.diagnosis.execute(diagnosis_context)
    
    yield {
        "type": "agent_thinking",
        "agent": diagnosis_identity,
        "payload": {"thought": "分析因果关系..."}
    }
    
    yield {
        "type": "agent_complete",
        "agent": diagnosis_identity,
        "payload": {"summary": diag_result.data.get("root_cause", "诊断完成")}
    }
    
    if not diag_result.success:
        yield {
            "type": "error",
            "payload": {"message": "Diagnosis failed", "stage": "diagnosis"}
        }
        return
    
    recovery_identity = {
        "id": f"recovery_{uuid.uuid4().hex[:8]}",
        "name": "RecoveryAgent",
        "display_name": "恢复Agent",
        "type": "recovery",
        "icon": "recovery"
    }
    
    yield {
        "type": "handoff",
        "agent": diagnosis_identity,
        "payload": {"to_agent": recovery_identity, "context": "诊断完成，生成恢复方案"}
    }
    
    yield {
        "type": "agent_start",
        "agent": recovery_identity,
        "payload": {"description": "生成恢复方案..."}
    }
    
    recovery_context = AgentContext(
        session_id=context.session_id,
        query=context.query,
        metadata={
            "root_cause": diag_result.data.get("root_cause", ""),
            "evidence_chain": diag_result.data.get("evidence_chain", []),
        }
    )
    rec_result = await self.recovery.execute(recovery_context)
    
    yield {
        "type": "agent_complete",
        "agent": recovery_identity,
        "payload": {"summary": rec_result.data.get("plan", "恢复方案已生成")}
    }
    
    yield {
        "type": "session_complete",
        "payload": {
            "status": "success",
            "summary": "根因已定位，恢复方案已生成",
            "agents_involved": ["InvestigationAgent", "DiagnosisAgent", "RecoveryAgent"]
        }
    }
```

- [ ] **Step 2: 创建WebSocket连接管理器**

创建 `backend/app/api/websocket.py`：

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Optional
import json
from datetime import datetime
import asyncio

from backend.app.agents.orchestrator import OrchestratorAgent
from backend.app.models.agent import ServerMessage, AgentIdentity
from backend.app.storage.database import get_db
from backend.app.storage.repositories.session_repo import SessionRepository

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._sequence: int = 0
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    def _get_sequence(self) -> int:
        self._sequence += 1
        return self._sequence
    
    async def send_event(self, session_id: str, event_type: str, payload: any, agent: Optional[dict] = None):
        if session_id in self.active_connections:
            message = {
                "type": event_type,
                "agent": agent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": self._get_sequence()
            }
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str
):
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                content = data.get("content", "")
                await handle_chat_message(session_id, content)
            
            elif data.get("type") == "stop":
                pass
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)

async def handle_chat_message(session_id: str, content: str):
    orchestrator = OrchestratorAgent()
    
    async for event in orchestrator.run_stream(session_id, content):
        await manager.send_event(
            session_id,
            event["type"],
            event.get("payload", {}),
            event.get("agent")
        )
```

- [ ] **Step 3: 在main.py中注册WebSocket路由**

在 `backend/app/main.py` 中添加：

```python
from backend.app.api.websocket import router as websocket_router

app.include_router(websocket_router, prefix="/api/v1")
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/websocket.py backend/app/main.py backend/app/agents/orchestrator.py
git commit -m "feat(ws): add WebSocket connection manager and run_stream method"
```

---

## Task 5: 后端数据源API

**Files:**
- Create: `backend/app/api/datasources.py`
- Create: `backend/app/services/connection_tester.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建连接测试服务**

创建 `backend/app/services/connection_tester.py`：

```python
import httpx
from typing import Tuple
from datetime import datetime
import time

async def test_prometheus(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/api/v1/status/config")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0

async def test_loki(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/ready")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0

async def test_influxdb(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/health")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0

async def test_jaeger(url: str, timeout: int = 5) -> Tuple[bool, str, int]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/api/services")
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return True, "连接成功", latency
            return False, f"HTTP {response.status_code}", latency
    except Exception as e:
        return False, str(e), 0

async def test_datasource(ds_type: str, url: str) -> Tuple[bool, str, int]:
    testers = {
        "prometheus": test_prometheus,
        "loki": test_loki,
        "influxdb": test_influxdb,
        "jaeger": test_jaeger
    }
    tester = testers.get(ds_type)
    if tester:
        return await tester(url)
    return False, "不支持的数据源类型", 0
```

- [ ] **Step 2: 创建数据源API**

创建 `backend/app/api/datasources.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.storage.database import get_db
from backend.app.storage.repositories.datasource_repo import DataSourceRepository
from backend.app.models.datasource import DataSource, DataSourceCreate, DataSourceUpdate, DataSourceTestResult
from backend.app.services.connection_tester import test_datasource

router = APIRouter()

@router.get("/datasources", response_model=List[DataSource])
async def list_datasources(db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    return repo.get_all()

@router.post("/datasources", response_model=DataSource)
async def create_datasource(data: DataSourceCreate, db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    return repo.create(data)

@router.get("/datasources/{ds_id}", response_model=DataSource)
async def get_datasource(ds_id: str, db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    ds = repo.get_by_id(ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds

@router.put("/datasources/{ds_id}", response_model=DataSource)
async def update_datasource(ds_id: str, data: DataSourceUpdate, db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    ds = repo.update(ds_id, data)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds

@router.delete("/datasources/{ds_id}")
async def delete_datasource(ds_id: str, db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    if not repo.delete(ds_id):
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"message": "删除成功"}

@router.post("/datasources/{ds_id}/test", response_model=DataSourceTestResult)
async def test_datasource_connection(ds_id: str, db: Session = Depends(get_db)):
    repo = DataSourceRepository(db)
    ds = repo.get_by_id(ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    success, message, latency = await test_datasource(ds.type, ds.url)
    
    status = "connected" if success else "error"
    repo.update_status(ds_id, status, None if success else message)
    
    return DataSourceTestResult(success=success, message=message, latency_ms=latency)
```

- [ ] **Step 3: 在main.py中注册数据源路由**

在 `backend/app/main.py` 中添加：

```python
from backend.app.api.datasources import router as datasources_router

app.include_router(datasources_router, prefix="/api/v1")
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/datasources.py backend/app/services/connection_tester.py backend/app/main.py
git commit -m "feat(api): add datasource management API with connection testing"
```

---

## Task 6: 后端知识管理API扩展

**Files:**
- Create: `backend/app/services/document_parser.py`
- Modify: `backend/app/api/knowledge.py`

- [ ] **Step 1: 创建文档解析服务**

创建 `backend/app/services/document_parser.py`：

```python
import os
import tempfile
from typing import Tuple, Optional
import uuid

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def parse_pdf(file_path: str) -> str:
    try:
        import PyPDF2
        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return "\n".join(text)
    except ImportError:
        return ""
    except Exception as e:
        raise ValueError(f"PDF解析失败: {str(e)}")

def parse_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        return ""
    except Exception as e:
        raise ValueError(f"DOCX解析失败: {str(e)}")

def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_document(file_path: str, filename: str) -> Tuple[str, str]:
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        content = parse_pdf(file_path)
    elif ext in [".doc", ".docx"]:
        content = parse_docx(file_path)
    elif ext == ".txt":
        content = parse_txt(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {ext}")
    
    return content, ext
```

- [ ] **Step 2: 扩展知识管理API**

修改 `backend/app/api/knowledge.py`，添加上传和搜索功能：

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import uuid

from backend.app.storage.database import get_db
from backend.app.storage.models import KnowledgeDB
from backend.app.models.knowledge import Knowledge, KnowledgeCreate, KnowledgeUpdate
from backend.app.services.document_parser import is_allowed_file, parse_document, MAX_FILE_SIZE

router = APIRouter()

@router.get("/knowledge", response_model=List[Knowledge])
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeDB)
    
    if type:
        query = query.filter(KnowledgeDB.type == type)
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(KnowledgeDB.tags.contains([tag]))
    
    if search:
        query = query.filter(KnowledgeDB.title.ilike(f"%{search}%"))
    
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()

@router.post("/knowledge", response_model=Knowledge)
async def create_knowledge(data: KnowledgeCreate, db: Session = Depends(get_db)):
    db_obj = KnowledgeDB(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/knowledge/tags", response_model=List[str])
async def list_knowledge_tags(db: Session = Depends(get_db)):
    all_knowledge = db.query(KnowledgeDB).all()
    tags = set()
    for k in all_knowledge:
        if k.tags:
            tags.update(k.tags)
    return sorted(list(tags))

@router.post("/knowledge/upload", response_model=Knowledge)
async def upload_knowledge(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    tags: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
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
        title=title or file.filename,
        content=parsed_content,
        type="file",
        file_url=file_url,
        file_name=file.filename,
        tags=[t.strip() for t in tags.split(",")] if tags else [],
        category=category
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj

@router.get("/knowledge/{knowledge_id}", response_model=Knowledge)
async def get_knowledge(knowledge_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(KnowledgeDB).filter(KnowledgeDB.id == knowledge_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="知识不存在")
    return db_obj

@router.put("/knowledge/{knowledge_id}", response_model=Knowledge)
async def update_knowledge(knowledge_id: str, data: KnowledgeUpdate, db: Session = Depends(get_db)):
    db_obj = db.query(KnowledgeDB).filter(KnowledgeDB.id == knowledge_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
    
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str, db: Session = Depends(get_db)):
    db_obj = db.query(KnowledgeDB).filter(KnowledgeDB.id == knowledge_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    db.delete(db_obj)
    db.commit()
    return {"message": "删除成功"}
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/document_parser.py backend/app/api/knowledge.py
git commit -m "feat(knowledge): add document upload and parsing support"
```

---

## Task 7: 前端类型定义

**Files:**
- Create: `frontend/src/types/agent.ts`
- Create: `frontend/src/types/datasource.ts`
- Create: `frontend/src/types/knowledge.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建Agent类型**

创建 `frontend/src/types/agent.ts`：

```typescript
export interface AgentIdentity {
  id: string;
  name: string;
  display_name: string;
  type: 'investigation' | 'diagnosis' | 'recovery' | 'orchestrator';
  icon?: string;
}

export interface ToolCallRecord {
  tool: string;
  params: Record<string, unknown>;
  result?: unknown;
  status: 'pending' | 'running' | 'success' | 'error';
  timestamp: string;
}

export interface AgentExecution {
  id: string;
  session_id: string;
  agent: AgentIdentity;
  status: 'idle' | 'running' | 'completed' | 'failed';
  thoughts: string[];
  tool_calls: ToolCallRecord[];
  result?: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface ServerMessage {
  type: string;
  agent?: AgentIdentity;
  payload: unknown;
  timestamp: string;
  sequence: number;
}

export interface TimelineNode {
  id: string;
  type: 'alert' | 'investigation' | 'diagnosis' | 'recovery' | 'complete';
  status: 'pending' | 'running' | 'completed' | 'failed';
  title: string;
  description?: string;
  timestamp: string;
  duration?: number;
  agent?: AgentIdentity;
}
```

- [ ] **Step 2: 创建数据源类型**

创建 `frontend/src/types/datasource.ts`：

```typescript
export interface DataSource {
  id: string;
  type: 'prometheus' | 'influxdb' | 'loki' | 'jaeger';
  name: string;
  url: string;
  auth_type: 'none' | 'basic' | 'bearer' | 'api_key';
  auth_config?: {
    username?: string;
    password?: string;
    token?: string;
    api_key?: string;
  };
  status: 'connected' | 'disconnected' | 'error' | 'not_configured';
  last_check?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreate {
  type: 'prometheus' | 'influxdb' | 'loki' | 'jaeger';
  name: string;
  url: string;
  auth_type?: 'none' | 'basic' | 'bearer' | 'api_key';
  auth_config?: Record<string, string>;
}

export interface DataSourceUpdate {
  name?: string;
  url?: string;
  auth_type?: string;
  auth_config?: Record<string, string>;
}

export interface DataSourceTestResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}
```

- [ ] **Step 3: 创建知识类型**

创建 `frontend/src/types/knowledge.ts`：

```typescript
export interface Knowledge {
  id: string;
  title: string;
  content: string;
  type: 'text' | 'file';
  file_url?: string;
  file_name?: string;
  tags: string[];
  category?: string;
  reference_count: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeCreate {
  title: string;
  content?: string;
  type?: 'text' | 'file';
  tags?: string[];
  category?: string;
}

export interface KnowledgeUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  category?: string;
}
```

- [ ] **Step 4: 扩展Session类型**

在 `frontend/src/types/index.ts` 中添加：

```typescript
export interface SessionListItem {
  id: string;
  title: string;
  trigger_type: string;
  trigger_source: string;
  status: 'investigating' | 'diagnosing' | 'recovering' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/types/agent.ts frontend/src/types/datasource.ts frontend/src/types/knowledge.ts frontend/src/types/index.ts
git commit -m "feat(types): add TypeScript types for agent, datasource, knowledge and extend Session"
```

---

## Task 8: 前端WebSocket服务

**Files:**
- Create: `frontend/src/services/websocket.ts`

- [ ] **Step 1: 创建WebSocket服务**

创建 `frontend/src/services/websocket.ts`：

```typescript
import { ServerMessage } from '../types/agent';

type MessageHandler = (message: ServerMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  private messageQueue: string[] = [];

  constructor(baseUrl: string) {
    this.url = baseUrl.replace('http', 'ws');
  }

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.url}/api/v1/ws/chat/${sessionId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyConnectionHandlers(true);
        
        this.messageQueue.forEach(msg => {
          this.ws?.send(msg);
        });
        this.messageQueue = [];
        
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data);
          this.emit(message.type, message);
          this.emit('*', message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.notifyConnectionHandlers(false);
        this.attemptReconnect(sessionId);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  private attemptReconnect(sessionId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(sessionId);
      }, delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(eventType: string, handler: MessageHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: MessageHandler) {
    if (this.handlers.has(eventType)) {
      this.handlers.get(eventType)!.delete(handler);
    }
  }

  onConnection(handler: ConnectionHandler) {
    this.connectionHandlers.add(handler);
  }

  offConnection(handler: ConnectionHandler) {
    this.connectionHandlers.delete(handler);
  }

  private emit(eventType: string, message: ServerMessage) {
    if (this.handlers.has(eventType)) {
      this.handlers.get(eventType)!.forEach(handler => handler(message));
    }
  }

  private notifyConnectionHandlers(connected: boolean) {
    this.connectionHandlers.forEach(handler => handler(connected));
  }

  sendChat(content: string) {
    const message = JSON.stringify({ type: 'chat', content });
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      this.messageQueue.push(message);
    }
  }

  sendStop() {
    const message = JSON.stringify({ type: 'stop' });
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
  }

  sendPing() {
    const message = JSON.stringify({ type: 'ping' });
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

let wsInstance: ChatWebSocket | null = null;

export function getWebSocket(): ChatWebSocket {
  if (!wsInstance) {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    wsInstance = new ChatWebSocket(apiUrl);
  }
  return wsInstance;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/services/websocket.ts
git commit -m "feat(ws): add WebSocket service with reconnection support"
```

---

## Task 9: 前端API服务

**Files:**
- Create: `frontend/src/services/datasourceApi.ts`
- Create: `frontend/src/services/knowledgeApi.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 在api.ts中添加axios实例默认导出**

在 `frontend/src/services/api.ts` 中添加默认导出：

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

export const sessionsApi = {
  list: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },
  create: async (data: { trigger_type: string; trigger_source: string }) => {
    const response = await api.post('/sessions', data);
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await api.delete(`/sessions/${id}`);
    return response.data;
  },
};

export const chatApi = {
  sendMessage: async (data: { session_id?: string; message: string }) => {
    const response = await api.post('/chat/message', data);
    return response.data;
  },
  streamMessage: async (data: { session_id?: string; message: string }) => {
    const response = await api.post('/chat/stream', data, {
      headers: { Accept: 'text/event-stream' },
      responseType: 'stream',
    });
    return response.data;
  },
};
```

- [ ] **Step 2: 创建数据源API服务**

创建 `frontend/src/services/datasourceApi.ts`：

```typescript
import api from './api';
import { DataSource, DataSourceCreate, DataSourceUpdate, DataSourceTestResult } from '../types/datasource';

const BASE_URL = '/datasources';

export const datasourceApi = {
  list: async (): Promise<DataSource[]> => {
    const response = await api.get(BASE_URL);
    return response.data;
  },

  get: async (id: string): Promise<DataSource> => {
    const response = await api.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  create: async (data: DataSourceCreate): Promise<DataSource> => {
    const response = await api.post(BASE_URL, data);
    return response.data;
  },

  update: async (id: string, data: DataSourceUpdate): Promise<DataSource> => {
    const response = await api.put(`${BASE_URL}/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`);
  },

  test: async (id: string): Promise<DataSourceTestResult> => {
    const response = await api.post(`${BASE_URL}/${id}/test`);
    return response.data;
  },
};
```

- [ ] **Step 3: 创建知识API服务**

创建 `frontend/src/services/knowledgeApi.ts`：

```typescript
import api from './api';
import { Knowledge, KnowledgeCreate, KnowledgeUpdate } from '../types/knowledge';

const BASE_URL = '/knowledge';

export const knowledgeApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    type?: string;
    tags?: string;
    search?: string;
  }): Promise<Knowledge[]> => {
    const response = await api.get(BASE_URL, { params });
    return response.data;
  },

  get: async (id: string): Promise<Knowledge> => {
    const response = await api.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  create: async (data: KnowledgeCreate): Promise<Knowledge> => {
    const response = await api.post(BASE_URL, data);
    return response.data;
  },

  update: async (id: string, data: KnowledgeUpdate): Promise<Knowledge> => {
    const response = await api.put(`${BASE_URL}/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`);
  },

  upload: async (file: File, metadata?: {
    title?: string;
    tags?: string;
    category?: string;
  }): Promise<Knowledge> => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata?.title) formData.append('title', metadata.title);
    if (metadata?.tags) formData.append('tags', metadata.tags);
    if (metadata?.category) formData.append('category', metadata.category);

    const response = await api.post(`${BASE_URL}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getTags: async (): Promise<string[]> => {
    const response = await api.get(`${BASE_URL}/tags`);
    return response.data;
  },
};
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/services/datasourceApi.ts frontend/src/services/knowledgeApi.ts frontend/src/services/api.ts
git commit -m "feat(api): add datasource and knowledge API services with axios instance"
```

---

## Task 10: 前端状态管理

**Files:**
- Create: `frontend/src/stores/agentStore.ts`
- Create: `frontend/src/stores/settingsStore.ts`
- Modify: `frontend/src/stores/sessionStore.ts`

- [ ] **Step 1: 创建Agent状态管理**

创建 `frontend/src/stores/agentStore.ts`：

```typescript
import { create } from 'zustand';
import { AgentIdentity, AgentExecution, TimelineNode, ServerMessage } from '../types/agent';

interface AgentState {
  agents: Record<string, AgentExecution>;
  currentAgent: string | null;
  timeline: TimelineNode[];
  sequence: number;
  isConnected: boolean;

  setCurrentAgent: (agentId: string | null) => void;
  handleMessage: (message: ServerMessage) => void;
  setConnected: (connected: boolean) => void;
  reset: () => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: {},
  currentAgent: null,
  timeline: [],
  sequence: 0,
  isConnected: false,

  setCurrentAgent: (agentId) => set({ currentAgent: agentId }),

  handleMessage: (message) => {
    const { agents, timeline, sequence } = get();
    const newAgents = { ...agents };
    let newTimeline = [...timeline];

    switch (message.type) {
      case 'orchestrator_status':
        newTimeline = [{
          id: 'orchestrator',
          type: 'alert',
          status: 'running',
          title: '编排器启动',
          timestamp: message.timestamp,
        }];
        break;

      case 'agent_start':
        if (message.agent) {
          const exec: AgentExecution = {
            id: message.agent.id,
            session_id: '',
            agent: message.agent,
            status: 'running',
            thoughts: [],
            tool_calls: [],
            started_at: message.timestamp,
          };
          newAgents[message.agent.id] = exec;
          
          newTimeline.push({
            id: message.agent.id,
            type: message.agent.type as TimelineNode['type'],
            status: 'running',
            title: message.agent.display_name,
            description: (message.payload as { description?: string })?.description,
            timestamp: message.timestamp,
            agent: message.agent,
          });
        }
        break;

      case 'agent_thinking':
        if (message.agent && newAgents[message.agent.id]) {
          const thought = (message.payload as { thought: string }).thought;
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            thoughts: [...newAgents[message.agent.id].thoughts, thought],
          };
        }
        break;

      case 'tool_call':
        if (message.agent && newAgents[message.agent.id]) {
          const toolCall = {
            ...(message.payload as object),
            status: 'running',
            timestamp: message.timestamp,
          } as AgentExecution['tool_calls'][0];
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            tool_calls: [...newAgents[message.agent.id].tool_calls, toolCall],
          };
        }
        break;

      case 'tool_result':
        if (message.agent && newAgents[message.agent.id]) {
          const toolCalls = [...newAgents[message.agent.id].tool_calls];
          const lastCall = toolCalls[toolCalls.length - 1];
          if (lastCall) {
            lastCall.result = (message.payload as { result: unknown }).result;
            lastCall.status = 'success';
          }
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            tool_calls: toolCalls,
          };
        }
        break;

      case 'agent_complete':
        if (message.agent && newAgents[message.agent.id]) {
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            status: 'completed',
            result: (message.payload as { summary?: string }).summary,
            completed_at: message.timestamp,
          };
          
          const timelineIdx = newTimeline.findIndex(n => n.id === message.agent!.id);
          if (timelineIdx >= 0) {
            newTimeline[timelineIdx] = {
              ...newTimeline[timelineIdx],
              status: 'completed',
              description: (message.payload as { summary?: string }).summary,
            };
          }
        }
        break;

      case 'handoff':
        const payload = message.payload as { to_agent: AgentIdentity; context: string };
        newTimeline.push({
          id: `handoff-${sequence}`,
          type: 'alert',
          status: 'completed',
          title: `${message.agent?.display_name} → ${payload.to_agent.display_name}`,
          description: payload.context,
          timestamp: message.timestamp,
        });
        break;

      case 'session_complete':
        newTimeline.push({
          id: 'complete',
          type: 'complete',
          status: 'completed',
          title: '会话完成',
          timestamp: message.timestamp,
        });
        break;
    }

    set({ agents: newAgents, timeline: newTimeline, sequence: sequence + 1 });
  },

  setConnected: (connected) => set({ isConnected: connected }),

  reset: () => set({
    agents: {},
    currentAgent: null,
    timeline: [],
    sequence: 0,
  }),
}));
```

- [ ] **Step 2: 创建设置状态管理**

创建 `frontend/src/stores/settingsStore.ts`：

```typescript
import { create } from 'zustand';
import { DataSource } from '../types/datasource';
import { Knowledge } from '../types/knowledge';

interface SettingsState {
  isOpen: boolean;
  activeTab: 'datasource' | 'knowledge';
  slidePanel: {
    open: boolean;
    mode: 'add' | 'edit';
    type: 'datasource' | 'knowledge';
    data?: DataSource | Knowledge;
  } | null;

  datasources: DataSource[];
  knowledge: Knowledge[];
  knowledgeTags: string[];

  openSettings: () => void;
  closeSettings: () => void;
  setActiveTab: (tab: 'datasource' | 'knowledge') => void;
  openSlidePanel: (mode: 'add' | 'edit', type: 'datasource' | 'knowledge', data?: DataSource | Knowledge) => void;
  closeSlidePanel: () => void;
  setDatasources: (datasources: DataSource[]) => void;
  setKnowledge: (knowledge: Knowledge[]) => void;
  setKnowledgeTags: (tags: string[]) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isOpen: false,
  activeTab: 'datasource',
  slidePanel: null,
  datasources: [],
  knowledge: [],
  knowledgeTags: [],

  openSettings: () => set({ isOpen: true }),
  closeSettings: () => set({ isOpen: false, slidePanel: null }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  openSlidePanel: (mode, type, data) => set({
    slidePanel: { open: true, mode, type, data },
  }),
  
  closeSlidePanel: () => set({ slidePanel: null }),
  
  setDatasources: (datasources) => set({ datasources }),
  setKnowledge: (knowledge) => set({ knowledge }),
  setKnowledgeTags: (tags) => set({ knowledgeTags: tags }),
}));
```

- [ ] **Step 3: 扩展会话状态管理**

修改 `frontend/src/stores/sessionStore.ts`，添加会话列表管理：

```typescript
import { create } from 'zustand';
import { Session, SessionListItem } from '../types';

interface SessionState {
  sessions: SessionListItem[];
  currentSession: Session | null;
  isLoading: boolean;
  searchQuery: string;

  setSessions: (sessions: SessionListItem[]) => void;
  setCurrentSession: (session: Session | null) => void;
  addSession: (session: SessionListItem) => void;
  updateSession: (session: SessionListItem) => void;
  removeSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  setSearchQuery: (query: string) => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  currentSession: null,
  isLoading: false,
  searchQuery: '',

  setSessions: (sessions) => set({ sessions }),
  
  setCurrentSession: (session) => set({ currentSession: session }),
  
  addSession: (session) => set((state) => ({
    sessions: [session, ...state.sessions],
  })),
  
  updateSession: (session) => set((state) => ({
    sessions: state.sessions.map((s) =>
      s.id === session.id ? session : s
    ),
    currentSession: state.currentSession?.id === session.id
      ? session as unknown as Session
      : state.currentSession,
  })),
  
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter((s) => s.id !== sessionId),
    currentSession: state.currentSession?.id === sessionId
      ? null
      : state.currentSession,
  })),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
}));
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/stores/agentStore.ts frontend/src/stores/settingsStore.ts frontend/src/stores/sessionStore.ts
git commit -m "feat(stores): add agent, settings stores and extend session store"
```

---

## Task 11: 前端Agent组件

**Files:**
- Create: `frontend/src/components/Agent/AgentProcessPanel.tsx`
- Create: `frontend/src/components/Agent/AgentCard.tsx`
- Create: `frontend/src/components/Agent/ThinkingStream.tsx`
- Create: `frontend/src/components/Agent/ToolCallItem.tsx`
- Create: `frontend/src/components/Agent/HandoffIndicator.tsx`

- [ ] **Step 1: 创建AgentProcessPanel组件**

创建 `frontend/src/components/Agent/AgentProcessPanel.tsx`：

```typescript
import React from 'react';
import { useAgentStore } from '../../stores/agentStore';
import AgentCard from './AgentCard';
import HandoffIndicator from './HandoffIndicator';

const AgentProcessPanel: React.FC = () => {
  const { agents, timeline } = useAgentStore();
  
  const agentList = Object.values(agents);
  const handoffs = timeline.filter(n => n.id.startsWith('handoff-'));

  return (
    <div className="agent-process-panel">
      {agentList.map((agent, index) => (
        <React.Fragment key={agent.id}>
          <AgentCard
            agent={agent.agent}
            status={agent.status}
            thoughts={agent.thoughts}
            toolCalls={agent.tool_calls}
            result={agent.result}
          />
          {index < agentList.length - 1 && handoffs[index] && (
            <HandoffIndicator
              from={agent.agent.display_name}
              to={handoffs[index].title.split(' → ')[1]}
              context={handoffs[index].description}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default AgentProcessPanel;
```

- [ ] **Step 2: 创建AgentCard组件**

创建 `frontend/src/components/Agent/AgentCard.tsx`：

```typescript
import React, { useState } from 'react';
import { Card, Tag, Collapse } from 'antd';
import {
  SearchOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { AgentIdentity, ToolCallRecord } from '../../types/agent';
import ThinkingStream from './ThinkingStream';
import ToolCallItem from './ToolCallItem';

interface AgentCardProps {
  agent: AgentIdentity;
  status: 'idle' | 'running' | 'completed' | 'failed';
  thoughts: string[];
  toolCalls: ToolCallRecord[];
  result?: string;
}

const agentIcons: Record<string, React.ReactNode> = {
  investigation: <SearchOutlined />,
  diagnosis: <ExperimentOutlined />,
  recovery: <MedicineBoxOutlined />,
};

const statusIcons: Record<string, React.ReactNode> = {
  idle: null,
  running: <LoadingOutlined spin />,
  completed: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  failed: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
};

const statusColors: Record<string, string> = {
  idle: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
};

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  status,
  thoughts,
  toolCalls,
  result,
}) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <Card
      className="agent-card"
      title={
        <div className="agent-card-header">
          <span className="agent-icon">
            {agentIcons[agent.type] || agent.icon}
          </span>
          <span className="agent-name">{agent.display_name}</span>
          <Tag color={statusColors[status]}>
            {statusIcons[status]} {status}
          </Tag>
        </div>
      }
      extra={
        <a onClick={() => setExpanded(!expanded)}>
          {expanded ? '折叠' : '展开'}
        </a>
      }
    >
      {expanded && (
        <div className="agent-card-content">
          {thoughts.length > 0 && (
            <ThinkingStream thoughts={thoughts} />
          )}
          
          {toolCalls.length > 0 && (
            <div className="tool-calls">
              {toolCalls.map((tc, idx) => (
                <ToolCallItem key={idx} toolCall={tc} />
              ))}
            </div>
          )}
          
          {result && (
            <div className="agent-result">
              <strong>结果：</strong>
              <p>{result}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default AgentCard;
```

- [ ] **Step 3: 创建ThinkingStream组件**

创建 `frontend/src/components/Agent/ThinkingStream.tsx`：

```typescript
import React from 'react';
import { Typography } from 'antd';
import { BulbOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ThinkingStreamProps {
  thoughts: string[];
}

const ThinkingStream: React.FC<ThinkingStreamProps> = ({ thoughts }) => {
  return (
    <div className="thinking-stream">
      {thoughts.map((thought, index) => (
        <div key={index} className="thought-item">
          <BulbOutlined style={{ marginRight: 8, color: '#faad14' }} />
          <Text type="secondary">{thought}</Text>
        </div>
      ))}
    </div>
  );
};

export default ThinkingStream;
```

- [ ] **Step 4: 创建ToolCallItem组件**

创建 `frontend/src/components/Agent/ToolCallItem.tsx`：

```typescript
import React from 'react';
import { Collapse, Tag } from 'antd';
import { ToolOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { ToolCallRecord } from '../../types/agent';

interface ToolCallItemProps {
  toolCall: ToolCallRecord;
}

const ToolCallItem: React.FC<ToolCallItemProps> = ({ toolCall }) => {
  const statusIcon = {
    pending: <LoadingOutlined />,
    running: <LoadingOutlined spin />,
    success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    error: <CheckCircleOutlined style={{ color: '#ff4d4f' }} />,
  };

  return (
    <Collapse
      className="tool-call-item"
      items={[
        {
          key: '1',
          label: (
            <div className="tool-call-header">
              <ToolOutlined style={{ marginRight: 8 }} />
              <span>{toolCall.tool}</span>
              <Tag>{toolCall.status}</Tag>
            </div>
          ),
          children: (
            <div className="tool-call-content">
              <div className="params">
                <strong>参数：</strong>
                <pre>{JSON.stringify(toolCall.params, null, 2)}</pre>
              </div>
              {toolCall.result && (
                <div className="result">
                  <strong>结果：</strong>
                  <pre>{JSON.stringify(toolCall.result, null, 2)}</pre>
                </div>
              )}
            </div>
          ),
        },
      ]}
    />
  );
};

export default ToolCallItem;
```

- [ ] **Step 5: 创建HandoffIndicator组件**

创建 `frontend/src/components/Agent/HandoffIndicator.tsx`：

```typescript
import React from 'react';
import { ArrowDownOutlined } from '@ant-design/icons';

interface HandoffIndicatorProps {
  from: string;
  to: string;
  context?: string;
}

const HandoffIndicator: React.FC<HandoffIndicatorProps> = ({
  from,
  to,
  context,
}) => {
  return (
    <div className="handoff-indicator">
      <ArrowDownOutlined style={{ fontSize: 16, color: '#1890ff' }} />
      <span className="handoff-text">
        {from} → {to}
      </span>
      {context && <span className="handoff-context">{context}</span>}
    </div>
  );
};

export default HandoffIndicator;
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/Agent/
git commit -m "feat(ui): add Agent process panel components"
```

---

## Task 12: 前端时间线组件

**Files:**
- Create: `frontend/src/components/Timeline/VerticalTimeline.tsx`
- Create: `frontend/src/components/Timeline/TimelineNode.tsx`

- [ ] **Step 1: 创建VerticalTimeline组件**

创建 `frontend/src/components/Timeline/VerticalTimeline.tsx`：

```typescript
import React from 'react';
import { Timeline } from 'antd';
import { useAgentStore } from '../../stores/agentStore';
import TimelineNode from './TimelineNode';

const VerticalTimeline: React.FC = () => {
  const { timeline } = useAgentStore();

  return (
    <div className="vertical-timeline">
      <Timeline
        items={timeline.map((node) => ({
          key: node.id,
          dot: <TimelineNode node={node} />,
          children: (
            <div className="timeline-content">
              <div className="timeline-header">
                <span className="timeline-title">{node.title}</span>
                <span className="timeline-time">{node.timestamp}</span>
              </div>
              {node.description && (
                <div className="timeline-description">{node.description}</div>
              )}
            </div>
          ),
        }))}
      />
    </div>
  );
};

export default VerticalTimeline;
```

- [ ] **Step 2: 创建TimelineNode组件**

创建 `frontend/src/components/Timeline/TimelineNode.tsx`：

```typescript
import React from 'react';
import {
  BellOutlined,
  SearchOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { TimelineNode as TimelineNodeType } from '../../types/agent';

interface TimelineNodeProps {
  node: TimelineNodeType;
}

const typeIcons: Record<string, React.ReactNode> = {
  alert: <BellOutlined />,
  investigation: <SearchOutlined />,
  diagnosis: <ExperimentOutlined />,
  recovery: <MedicineBoxOutlined />,
  complete: <CheckCircleOutlined />,
};

const statusColors: Record<string, string> = {
  pending: '#d9d9d9',
  running: '#1890ff',
  completed: '#52c41a',
  failed: '#ff4d4f',
};

const TimelineNode: React.FC<TimelineNodeProps> = ({ node }) => {
  const icon = typeIcons[node.type] || <CheckCircleOutlined />;
  const color = statusColors[node.status];
  
  return (
    <div
      className="timeline-node-dot"
      style={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        backgroundColor: color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
      }}
    >
      {node.status === 'running' ? (
        <LoadingOutlined spin />
      ) : (
        icon
      )}
    </div>
  );
};

export default TimelineNode;
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Timeline/
git commit -m "feat(ui): add vertical timeline components"
```

---

## Task 13: 前端会话侧边栏组件

**Files:**
- Create: `frontend/src/components/Session/SessionSidebar.tsx`
- Create: `frontend/src/components/Session/SessionList.tsx`
- Create: `frontend/src/components/Session/SessionToolbar.tsx`

- [ ] **Step 1: 创建SessionToolbar组件**

创建 `frontend/src/components/Session/SessionToolbar.tsx`：

```typescript
import React from 'react';
import { Input, Button, Tooltip } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';

interface SessionToolbarProps {
  searchQuery: string;
  onSearch: (query: string) => void;
  onNewSession: () => void;
}

const SessionToolbar: React.FC<SessionToolbarProps> = ({
  searchQuery,
  onSearch,
  onNewSession,
}) => {
  return (
    <div className="session-toolbar">
      <Input
        placeholder="搜索会话..."
        prefix={<SearchOutlined />}
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value)}
        className="session-search"
      />
      <Tooltip title="新建会话">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={onNewSession}
        />
      </Tooltip>
    </div>
  );
};

export default SessionToolbar;
```

- [ ] **Step 2: 创建SessionList组件**

创建 `frontend/src/components/Session/SessionList.tsx`：

```typescript
import React from 'react';
import { List, Tag, Popconfirm, Button } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { SessionListItem } from '../../types';

interface SessionListProps {
  sessions: SessionListItem[];
  currentSessionId: string | null;
  onSelect: (session: SessionListItem) => void;
  onDelete: (sessionId: string) => void;
}

const statusLabels: Record<string, string> = {
  investigating: '调查中',
  diagnosing: '诊断中',
  recovering: '恢复中',
  completed: '已完成',
  failed: '失败',
};

const statusColors: Record<string, string> = {
  investigating: 'processing',
  diagnosing: 'processing',
  recovering: 'processing',
  completed: 'success',
  failed: 'error',
};

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
}) => {
  const groupByDate = (sessions: SessionListItem[]) => {
    const groups: Record<string, SessionListItem[]> = {};
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();

    sessions.forEach((session) => {
      const date = new Date(session.created_at).toDateString();
      let label = date;
      
      if (date === today) label = '今天';
      else if (date === yesterday) label = '昨天';
      
      if (!groups[label]) groups[label] = [];
      groups[label].push(session);
    });

    return groups;
  };

  const grouped = groupByDate(sessions);

  return (
    <div className="session-list">
      {Object.entries(grouped).map(([date, items]) => (
        <div key={date} className="session-group">
          <div className="session-group-label">{date}</div>
          <List
            dataSource={items}
            renderItem={(session) => (
              <List.Item
                className={`session-item ${
                  session.id === currentSessionId ? 'active' : ''
                }`}
                onClick={() => onSelect(session)}
              >
                <div className="session-item-content">
                  <div className="session-title">{session.title || '新会话'}</div>
                  <div className="session-meta">
                    <Tag color={statusColors[session.status]}>
                      {statusLabels[session.status]}
                    </Tag>
                    <span className="session-time">
                      {new Date(session.updated_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <Popconfirm
                  title="确定删除此会话？"
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    onDelete(session.id);
                  }}
                >
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    size="small"
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>
              </List.Item>
            )}
          />
        </div>
      ))}
    </div>
  );
};

export default SessionList;
```

- [ ] **Step 3: 创建SessionSidebar组件**

创建 `frontend/src/components/Session/SessionSidebar.tsx`：

```typescript
import React, { useEffect } from 'react';
import { Button, message } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { useSessionStore } from '../../stores/sessionStore';
import { useSettingsStore } from '../../stores/settingsStore';
import SessionToolbar from './SessionToolbar';
import SessionList from './SessionList';
import { sessionsApi } from '../../services/api';

const SessionSidebar: React.FC = () => {
  const {
    sessions,
    currentSession,
    searchQuery,
    setSessions,
    setCurrentSession,
    setSearchQuery,
    removeSession,
  } = useSessionStore();
  
  const { openSettings } = useSettingsStore();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await sessionsApi.list();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleNewSession = async () => {
    try {
      const session = await sessionsApi.create({
        trigger_type: 'manual',
        trigger_source: 'user',
      });
      setCurrentSession(session);
      loadSessions();
    } catch (error) {
      console.error('Failed to create session:', error);
      message.error('创建会话失败');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await sessionsApi.delete(sessionId);
      removeSession(sessionId);
      message.success('删除成功');
    } catch (error) {
      console.error('Failed to delete session:', error);
      message.error('删除失败');
    }
  };

  const filteredSessions = searchQuery
    ? sessions.filter((s) =>
        s.title?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : sessions;

  return (
    <div className="session-sidebar">
      <div className="session-sidebar-header">
        <h2>NyxAI</h2>
      </div>
      
      <SessionToolbar
        searchQuery={searchQuery}
        onSearch={setSearchQuery}
        onNewSession={handleNewSession}
      />
      
      <SessionList
        sessions={filteredSessions}
        currentSessionId={currentSession?.id || null}
        onSelect={(s) => setCurrentSession(s as any)}
        onDelete={handleDeleteSession}
      />
      
      <div className="session-sidebar-footer">
        <Button
          icon={<SettingOutlined />}
          block
          onClick={openSettings}
        >
          设置
        </Button>
      </div>
    </div>
  );
};

export default SessionSidebar;
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/Session/
git commit -m "feat(ui): add session sidebar components"
```

---

## Task 14: 前端设置页面组件

**Files:**
- Create: `frontend/src/components/Settings/SettingsPage.tsx`
- Create: `frontend/src/components/Settings/SettingsSidebar.tsx`
- Create: `frontend/src/components/Settings/SlidePanel.tsx`

- [ ] **Step 1: 创建SettingsSidebar组件**

创建 `frontend/src/components/Settings/SettingsSidebar.tsx`：

```typescript
import React from 'react';
import { DatabaseOutlined, BookOutlined } from '@ant-design/icons';
import { useSettingsStore } from '../../stores/settingsStore';

const SettingsSidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useSettingsStore();

  const tabs = [
    { key: 'datasource', label: '数据源', icon: <DatabaseOutlined /> },
    { key: 'knowledge', label: '知识', icon: <BookOutlined /> },
  ];

  return (
    <div className="settings-sidebar">
      {tabs.map((tab) => (
        <div
          key={tab.key}
          className={`settings-tab ${activeTab === tab.key ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.key as 'datasource' | 'knowledge')}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </div>
      ))}
    </div>
  );
};

export default SettingsSidebar;
```

- [ ] **Step 2: 创建SlidePanel组件**

创建 `frontend/src/components/Settings/SlidePanel.tsx`：

```typescript
import React from 'react';
import { Drawer } from 'antd';
import { useSettingsStore } from '../../stores/settingsStore';
import DataSourceForm from './DataSourceForm';
import KnowledgeForm from './KnowledgeForm';

const SlidePanel: React.FC = () => {
  const { slidePanel, closeSlidePanel } = useSettingsStore();

  if (!slidePanel?.open) return null;

  return (
    <Drawer
      title={slidePanel.mode === 'add' ? '添加' : '编辑'}
      placement="right"
      width={400}
      open={slidePanel.open}
      onClose={closeSlidePanel}
      destroyOnClose
    >
      {slidePanel.type === 'datasource' ? (
        <DataSourceForm
          mode={slidePanel.mode}
          data={slidePanel.data}
          onSuccess={closeSlidePanel}
        />
      ) : (
        <KnowledgeForm
          mode={slidePanel.mode}
          data={slidePanel.data}
          onSuccess={closeSlidePanel}
        />
      )}
    </Drawer>
  );
};

export default SlidePanel;
```

- [ ] **Step 3: 创建SettingsPage组件**

创建 `frontend/src/components/Settings/SettingsPage.tsx`：

```typescript
import React, { useEffect } from 'react';
import { Modal } from 'antd';
import { useSettingsStore } from '../../stores/settingsStore';
import SettingsSidebar from './SettingsSidebar';
import DataSourceList from './DataSourceList';
import KnowledgeList from './KnowledgeList';
import SlidePanel from './SlidePanel';
import { datasourceApi } from '../../services/datasourceApi';
import { knowledgeApi } from '../../services/knowledgeApi';

const SettingsPage: React.FC = () => {
  const {
    isOpen,
    closeSettings,
    activeTab,
    setDatasources,
    setKnowledge,
    setKnowledgeTags,
  } = useSettingsStore();

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      const [datasources, knowledge, tags] = await Promise.all([
        datasourceApi.list(),
        knowledgeApi.list(),
        knowledgeApi.getTags(),
      ]);
      setDatasources(datasources);
      setKnowledge(knowledge);
      setKnowledgeTags(tags);
    } catch (error) {
      console.error('Failed to load settings data:', error);
    }
  };

  return (
    <>
      <Modal
        className="settings-modal"
        open={isOpen}
        onCancel={closeSettings}
        footer={null}
        width="100%"
        style={{ top: 0, maxWidth: '100vw' }}
        closable
        title="设置"
      >
        <div className="settings-page">
          <SettingsSidebar />
          <div className="settings-content">
            {activeTab === 'datasource' ? (
              <DataSourceList />
            ) : (
              <KnowledgeList />
            )}
          </div>
        </div>
      </Modal>
      <SlidePanel />
    </>
  );
};

export default SettingsPage;
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/Settings/SettingsPage.tsx frontend/src/components/Settings/SettingsSidebar.tsx frontend/src/components/Settings/SlidePanel.tsx
git commit -m "feat(ui): add settings page base components"
```

---

## Task 15: 前端数据源和知识列表组件

**Files:**
- Create: `frontend/src/components/Settings/DataSourceList.tsx`
- Create: `frontend/src/components/Settings/DataSourceForm.tsx`
- Create: `frontend/src/components/Settings/KnowledgeList.tsx`
- Create: `frontend/src/components/Settings/KnowledgeForm.tsx`

- [ ] **Step 1: 创建DataSourceList组件**

创建 `frontend/src/components/Settings/DataSourceList.tsx`：

```typescript
import React from 'react';
import { List, Tag, Button, Space, message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import { useSettingsStore } from '../../stores/settingsStore';
import { datasourceApi } from '../../services/datasourceApi';
import { DataSource } from '../../types/datasource';

const statusColors: Record<string, string> = {
  connected: 'success',
  disconnected: 'warning',
  error: 'error',
  not_configured: 'default',
};

const statusLabels: Record<string, string> = {
  connected: '已连接',
  disconnected: '已断开',
  error: '连接失败',
  not_configured: '未配置',
};

const DataSourceList: React.FC = () => {
  const { datasources, openSlidePanel, setDatasources } = useSettingsStore();

  const handleTest = async (ds: DataSource) => {
    try {
      const result = await datasourceApi.test(ds.id);
      if (result.success) {
        message.success(`连接成功 (${result.latency_ms}ms)`);
      } else {
        message.error(`连接失败: ${result.message}`);
      }
      const updated = await datasourceApi.list();
      setDatasources(updated);
    } catch (error) {
      message.error('测试失败');
    }
  };

  const handleDelete = async (ds: DataSource) => {
    try {
      await datasourceApi.delete(ds.id);
      const updated = await datasourceApi.list();
      setDatasources(updated);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  return (
    <div className="datasource-list">
      <div className="datasource-header">
        <h3>数据源管理</h3>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => openSlidePanel('add', 'datasource')}
        >
          添加数据源
        </Button>
      </div>
      
      <List
        dataSource={datasources}
        renderItem={(ds) => (
          <List.Item
            actions={[
              <Button
                key="test"
                type="link"
                icon={<ApiOutlined />}
                onClick={() => handleTest(ds)}
              >
                测试
              </Button>,
              <Button
                key="edit"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openSlidePanel('edit', 'datasource', ds)}
              >
                编辑
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(ds)}
              >
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{ds.name}</span>
                  <Tag color={statusColors[ds.status]}>
                    {statusLabels[ds.status]}
                  </Tag>
                </Space>
              }
              description={
                <div>
                  <div>{ds.url}</div>
                  {ds.error_message && (
                    <div style={{ color: '#ff4d4f' }}>{ds.error_message}</div>
                  )}
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );
};

export default DataSourceList;
```

- [ ] **Step 2: 创建DataSourceForm组件**

创建 `frontend/src/components/Settings/DataSourceForm.tsx`：

```typescript
import React from 'react';
import { Form, Input, Select, Button, message } from 'antd';
import { DataSource } from '../../types/datasource';
import { datasourceApi } from '../../services/datasourceApi';
import { useSettingsStore } from '../../stores/settingsStore';

interface DataSourceFormProps {
  mode: 'add' | 'edit';
  data?: DataSource;
  onSuccess: () => void;
}

const DataSourceForm: React.FC<DataSourceFormProps> = ({
  mode,
  data,
  onSuccess,
}) => {
  const { setDatasources } = useSettingsStore();
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    try {
      if (mode === 'add') {
        await datasourceApi.create(values);
        message.success('添加成功');
      } else {
        await datasourceApi.update(data!.id, values);
        message.success('更新成功');
      }
      const updated = await datasourceApi.list();
      setDatasources(updated);
      onSuccess();
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={data || { auth_type: 'none' }}
      onFinish={handleSubmit}
    >
      <Form.Item
        name="type"
        label="数据源类型"
        rules={[{ required: true }]}
      >
        <Select disabled={mode === 'edit'}>
          <Select.Option value="prometheus">Prometheus</Select.Option>
          <Select.Option value="influxdb">InfluxDB</Select.Option>
          <Select.Option value="loki">Loki</Select.Option>
          <Select.Option value="jaeger">Jaeger</Select.Option>
        </Select>
      </Form.Item>
      
      <Form.Item
        name="name"
        label="名称"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>
      
      <Form.Item
        name="url"
        label="URL"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>
      
      <Form.Item name="auth_type" label="认证方式">
        <Select>
          <Select.Option value="none">无认证</Select.Option>
          <Select.Option value="basic">Basic Auth</Select.Option>
          <Select.Option value="bearer">Bearer Token</Select.Option>
          <Select.Option value="api_key">API Key</Select.Option>
        </Select>
      </Form.Item>
      
      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          保存
        </Button>
      </Form.Item>
    </Form>
  );
};

export default DataSourceForm;
```

- [ ] **Step 3: 创建KnowledgeList组件**

创建 `frontend/src/components/Settings/KnowledgeList.tsx`：

```typescript
import React, { useState } from 'react';
import { List, Tag, Button, Space, Input, Select, Upload, message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useSettingsStore } from '../../stores/settingsStore';
import { knowledgeApi } from '../../services/knowledgeApi';
import { Knowledge } from '../../types/knowledge';

const KnowledgeList: React.FC = () => {
  const { knowledge, knowledgeTags, openSlidePanel, setKnowledge } = useSettingsStore();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const handleUpload = async (file: File) => {
    try {
      await knowledgeApi.upload(file);
      const updated = await knowledgeApi.list();
      setKnowledge(updated);
      message.success('上传成功');
    } catch (error) {
      message.error('上传失败');
    }
    return false;
  };

  const handleDelete = async (item: Knowledge) => {
    try {
      await knowledgeApi.delete(item.id);
      const updated = await knowledgeApi.list();
      setKnowledge(updated);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const filtered = knowledge.filter((k) => {
    const matchSearch = k.title.toLowerCase().includes(search.toLowerCase());
    const matchType = typeFilter === 'all' || k.type === typeFilter;
    return matchSearch && matchType;
  });

  return (
    <div className="knowledge-list">
      <div className="knowledge-toolbar">
        <Space>
          <Input
            placeholder="搜索知识..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 200 }}
          />
          <Select value={typeFilter} onChange={setTypeFilter} style={{ width: 120 }}>
            <Select.Option value="all">全部类型</Select.Option>
            <Select.Option value="text">文本</Select.Option>
            <Select.Option value="file">文件</Select.Option>
          </Select>
        </Space>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openSlidePanel('add', 'knowledge')}
          >
            添加
          </Button>
          <Upload
            beforeUpload={handleUpload}
            showUploadList={false}
            accept=".pdf,.doc,.docx,.txt"
          >
            <Button icon={<UploadOutlined />}>上传</Button>
          </Upload>
        </Space>
      </div>
      
      <List
        dataSource={filtered}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                key="edit"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openSlidePanel('edit', 'knowledge', item)}
              >
                编辑
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(item)}
              >
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{item.title}</span>
                  <Tag>{item.type === 'text' ? '文本' : '文件'}</Tag>
                </Space>
              }
              description={
                <div>
                  <div>
                    标签: {item.tags.map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </div>
                  <div>
                    更新: {new Date(item.updated_at).toLocaleDateString()} | 
                    引用: {item.reference_count}次
                  </div>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );
};

export default KnowledgeList;
```

- [ ] **Step 4: 创建KnowledgeForm组件**

创建 `frontend/src/components/Settings/KnowledgeForm.tsx`：

```typescript
import React from 'react';
import { Form, Input, Select, Button, message } from 'antd';
import { Knowledge } from '../../types/knowledge';
import { knowledgeApi } from '../../services/knowledgeApi';
import { useSettingsStore } from '../../stores/settingsStore';

interface KnowledgeFormProps {
  mode: 'add' | 'edit';
  data?: Knowledge;
  onSuccess: () => void;
}

const KnowledgeForm: React.FC<KnowledgeFormProps> = ({
  mode,
  data,
  onSuccess,
}) => {
  const { setKnowledge, knowledgeTags } = useSettingsStore();
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    try {
      if (mode === 'add') {
        await knowledgeApi.create(values);
        message.success('添加成功');
      } else {
        await knowledgeApi.update(data!.id, values);
        message.success('更新成功');
      }
      const updated = await knowledgeApi.list();
      setKnowledge(updated);
      onSuccess();
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={data || { type: 'text', tags: [] }}
      onFinish={handleSubmit}
    >
      <Form.Item
        name="title"
        label="标题"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>
      
      <Form.Item name="type" label="类型">
        <Select>
          <Select.Option value="text">文本</Select.Option>
          <Select.Option value="file">文件</Select.Option>
        </Select>
      </Form.Item>
      
      <Form.Item name="content" label="内容">
        <Input.TextArea rows={6} />
      </Form.Item>
      
      <Form.Item name="tags" label="标签">
        <Select mode="tags" placeholder="输入标签">
          {knowledgeTags.map((tag) => (
            <Select.Option key={tag} value={tag}>
              {tag}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>
      
      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          保存
        </Button>
      </Form.Item>
    </Form>
  );
};

export default KnowledgeForm;
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/Settings/DataSourceList.tsx frontend/src/components/Settings/DataSourceForm.tsx frontend/src/components/Settings/KnowledgeList.tsx frontend/src/components/Settings/KnowledgeForm.tsx
git commit -m "feat(ui): add datasource and knowledge list/form components"
```

---

## Task 16: 集成到主应用

**Files:**
- Modify: `frontend/src/components/Chat/ChatWindow.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 修改ChatWindow集成WebSocket和Agent组件**

修改 `frontend/src/components/Chat/ChatWindow.tsx`：

```typescript
import React, { useEffect, useState } from 'react';
import { Input, Button, Spin } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useSessionStore } from '../../stores/sessionStore';
import { useAgentStore } from '../../stores/agentStore';
import { getWebSocket } from '../../services/websocket';
import AgentProcessPanel from '../Agent/AgentProcessPanel';
import VerticalTimeline from '../Timeline/VerticalTimeline';

const ChatWindow: React.FC = () => {
  const { currentSession } = useSessionStore();
  const { isConnected, handleMessage, setConnected, reset } = useAgentStore();
  const [input, setInput] = useState('');
  const [ws, setWs] = useState(getWebSocket());

  useEffect(() => {
    if (currentSession) {
      reset();
      ws.connect(currentSession.id).then(() => {
        setConnected(true);
      });

      ws.on('*', (message) => {
        handleMessage(message);
      });

      ws.onConnection((connected) => {
        setConnected(connected);
      });
    }

    return () => {
      ws.disconnect();
    };
  }, [currentSession?.id]);

  const handleSend = () => {
    if (input.trim() && ws.isConnected()) {
      ws.sendChat(input.trim());
      setInput('');
    }
  };

  if (!currentSession) {
    return (
      <div className="chat-window-empty">
        <p>选择或创建一个会话开始对话</p>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-content">
        <AgentProcessPanel />
        <VerticalTimeline />
      </div>
      
      <div className="chat-input">
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={!isConnected}
        >
          发送
        </Button>
      </div>
    </div>
  );
};

export default ChatWindow;
```

- [ ] **Step 2: 修改App.tsx集成侧边栏和设置页面**

修改 `frontend/src/App.tsx`：

```typescript
import React from 'react';
import { Layout } from 'antd';
import SessionSidebar from './components/Session/SessionSidebar';
import ChatWindow from './components/Chat/ChatWindow';
import SettingsPage from './components/Settings/SettingsPage';
import './App.css';

const { Sider, Content } = Layout;

const App: React.FC = () => {
  return (
    <Layout className="app-layout">
      <Sider width={280} className="app-sider">
        <SessionSidebar />
      </Sider>
      <Content className="app-content">
        <ChatWindow />
      </Content>
      <SettingsPage />
    </Layout>
  );
};

export default App;
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Chat/ChatWindow.tsx frontend/src/App.tsx
git commit -m "feat(integration): integrate WebSocket, Agent components, and Settings page"
```

---

## Task 17: 添加样式

**Files:**
- Modify: `frontend/src/App.css`

- [ ] **Step 1: 添加全局样式**

在 `frontend/src/App.css` 中添加：

```css
.app-layout {
  height: 100vh;
}

.app-sider {
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

.app-content {
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.session-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.session-sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.session-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
}

.session-search {
  flex: 1;
}

.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-group-label {
  padding: 8px 16px;
  color: #999;
  font-size: 12px;
}

.session-item {
  cursor: pointer;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.session-item.active {
  background: #e6f7ff;
}

.session-item:hover {
  background: #fafafa;
}

.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.agent-process-panel {
  margin-bottom: 16px;
}

.agent-card {
  margin-bottom: 12px;
}

.agent-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vertical-timeline {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.settings-modal .ant-modal-content {
  height: 100vh;
}

.settings-modal .ant-modal-body {
  height: calc(100vh - 110px);
  padding: 0;
}

.settings-page {
  display: flex;
  height: 100%;
}

.settings-sidebar {
  width: 200px;
  border-right: 1px solid #f0f0f0;
  padding: 16px 0;
}

.settings-tab {
  padding: 12px 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-tab.active {
  background: #e6f7ff;
  color: #1890ff;
}

.settings-tab:hover {
  background: #fafafa;
}

.settings-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.datasource-header,
.knowledge-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.handoff-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: #1890ff;
}

.thinking-stream {
  margin-bottom: 12px;
}

.thought-item {
  margin-bottom: 8px;
}

.tool-call-item {
  margin-bottom: 8px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-result {
  margin-top: 12px;
  padding: 8px;
  background: #f6ffed;
  border-radius: 4px;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.css
git commit -m "style: add global styles for all components"
```

---

## Task 18: 最终验证

- [ ] **Step 1: 运行后端测试**

```bash
cd backend
pytest tests/ -v
```

- [ ] **Step 2: 运行前端类型检查**

```bash
cd frontend
npm run typecheck
```

- [ ] **Step 3: 运行前端构建**

```bash
cd frontend
npm run build
```

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: complete Agent chat enhancement implementation"
```
