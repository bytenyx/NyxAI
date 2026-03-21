# Agent对话系统增强设计文档

## 概述

本设计文档描述了NyxAI Agent对话系统的增强功能，包括：
- 对话框实时展示Agent分析调查过程
- 历史会话加载与新建会话
- 在线页面管理数据源和知识

## 功能需求

### 1. Agent思考过程实时展示

- 展示完整的Agent思考过程（思考链、工具调用、中间结果）
- 可视化流程图（竖排时间线）
- 区分不同Agent的执行过程

### 2. 会话管理

- 侧边栏会话列表布局
- 支持历史会话加载
- 支持新建会话
- 会话搜索功能

### 3. 数据源管理

- 数据源配置管理（添加、编辑、删除）
- 连接测试与状态监控
- 数据预览与查询

### 4. 知识管理

- 知识条目CRUD
- 文档上传与解析
- 知识分类与搜索

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React)                             │
├─────────────┬───────────────────────────────────────────────────┤
│  会话侧边栏  │              对话主区域                           │
│             │  ┌─────────────────────────────────────────────┐  │
│ ┌─────────┐ │  │              Agent思考过程                   │  │
│ │会话列表  │ │  │               (实时流)                       │  │
│ │         │ │  ├─────────────────────────────────────────────┤  │
│ │         │ │  │              可视化流程图                    │  │
│ │         │ │  │               (时间线)                       │  │
│ ├─────────┤ │  ├─────────────────────────────────────────────┤  │
│ │ 🔍 ➕   │ │  │              消息输入区                      │  │
│ └─────────┘ │  └─────────────────────────────────────────────┘  │
│ ─────────── │                                                   │
│ ┌─────────┐ │                                                   │
│ │ ⚙ 设置  │ │                                                   │
│ └─────────┘ │                                                   │
└─────────────┴───────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │ 点击设置按钮弹出   │
                    │                   │
                    │ ┌───────────────┐ │
                    │ │📊数据源│📚知识│ │
                    │ ├───────────────┤ │
                    │ │ 管理内容...    │ │
                    │ └───────────────┘ │
                    └───────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | React + TypeScript + Vite |
| UI组件库 | Ant Design |
| 状态管理 | Zustand |
| 实时通信 | WebSocket |
| 后端框架 | FastAPI (Python) |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 向量数据库 | Chroma |
| 文档解析 | PyPDF2, python-docx |

## 详细设计

### 1. WebSocket实时通信

#### 1.1 消息类型定义

```typescript
// Agent标识信息（每条消息必带）
interface AgentIdentity {
  id: string;           // 唯一标识，如 "investigation_001"
  name: string;         // 技术名称，如 "InvestigationAgent"
  display_name: string; // 显示名称，如 "调查Agent"
  type: 'investigation' | 'diagnosis' | 'recovery' | 'orchestrator';
  icon?: string;        // 图标标识，如 "search", "diagnosis", "recovery"
}

// 服务端 -> 客户端消息
interface ServerMessage {
  type: 
    | 'orchestrator_status'  // 编排器状态
    | 'agent_start'          // Agent开始执行
    | 'agent_thinking'       // Agent思考过程
    | 'agent_action'         // Agent执行动作
    | 'agent_result'         // Agent阶段结果
    | 'agent_complete'       // Agent完成
    | 'tool_call'            // 工具调用
    | 'tool_result'          // 工具返回
    | 'handoff'              // Agent交接
    | 'evidence_update'      // 证据更新
    | 'flow_update'          // 流程图更新
    | 'session_complete'     // 整个会话完成
    | 'error'                // 错误
    | 'pong';                // 心跳响应
  
  agent?: AgentIdentity;     // Agent标识（除部分消息类型外必带）
  payload: any;
  timestamp: string;
  sequence: number;          // 消息序号
}
```

#### 1.2 消息流程示例

```
1. orchestrator_status -> 编排器启动
2. agent_start (InvestigationAgent) -> 调查Agent开始
3. agent_thinking (InvestigationAgent) -> 思考过程
4. tool_call (InvestigationAgent) -> 调用工具
5. tool_result (InvestigationAgent) -> 工具返回
6. agent_complete (InvestigationAgent) -> 调查Agent完成
7. handoff (InvestigationAgent -> DiagnosisAgent) -> Agent交接
8. agent_start (DiagnosisAgent) -> 诊断Agent开始
...
9. session_complete -> 会话完成
```

#### 1.3 后端WebSocket实现

```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_agent_event(self, session_id: str, event: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(event)

manager = ConnectionManager()

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket, 
    session_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "chat":
                async for event in orchestrator.run_stream(data["payload"]):
                    await websocket.send_json(event)
            elif data["type"] == "stop":
                orchestrator.stop()
            elif data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

### 2. Agent思考过程UI

#### 2.1 组件结构

```
ChatWindow/
├── AgentProcessPanel/           # Agent实时思考过程面板
│   ├── AgentCard.tsx            # 单个Agent卡片
│   │   ├── AgentHeader          # Agent名称、状态、图标
│   │   ├── ThinkingStream       # 思考过程流式展示
│   │   ├── ToolCallItem         # 工具调用项
│   │   └── AgentResult          # Agent结果
│   └── HandoffIndicator.tsx     # Agent交接指示器
│
├── VerticalTimeline/            # 竖排时间线
│   ├── TimelineContainer.tsx    # 时间线容器
│   └── TimelineNode.tsx         # 时间线节点
│
└── MessageInput/                # 消息输入区
```

#### 2.2 AgentCard组件

```typescript
interface AgentCardProps {
  agent: AgentIdentity;
  status: 'idle' | 'running' | 'completed' | 'failed';
  thoughts: string[];
  toolCalls: ToolCallRecord[];
  result?: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
}

interface ToolCallRecord {
  tool: string;
  params: any;
  result?: any;
  status: 'pending' | 'running' | 'success' | 'error';
  timestamp: string;
}
```

#### 2.3 竖排时间线

```typescript
interface TimelineNode {
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

**视觉效果：**

```
       ┌──────────────────────────────────┐
       │ 📢 告警触发                       │ T+0s
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │ 🔍 调查Agent              ✓ 完成  │ T+5s
       │    发现API响应时间异常            │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │ 🔬 诊断Agent              🔄 进行中│ T+15s
       │    分析因果关系...                │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │ 💊 恢复Agent              ⏳ 等待  │ T+?s
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │ ✅ 会话完成                       │ T+?s
       └──────────────────────────────────┘
```

### 3. 会话管理

#### 3.1 侧边栏布局

```
┌──────────────────────┐
│                      │
│   NyxAI              │
│   ──────────────     │
│                      │
│   ┌──────────────┬───┤
│   │ 🔍 搜索会话   │ ➕│
│   └──────────────┴───┤
│                      │
│   今天               │
│   ├─ 📋 API异常调查  │
│   │   10:30 完成     │
│   │                  │
│   └─ 📋 数据库慢查询 │
│       09:15 完成     │
│                      │
│   昨天               │
│   └─ 📋 内存泄漏分析 │
│       16:20 完成     │
│                      │
│   ──────────────     │
│   ┌──────────────┐   │
│   │ ⚙ 设置       │   │
│   └──────────────┘   │
│                      │
└──────────────────────┘
```

#### 3.2 数据结构

```typescript
interface SessionListItem {
  id: string;
  title: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

interface SessionStore {
  sessions: SessionListItem[];
  currentSessionId: string | null;
  isLoading: boolean;
  
  loadSessions: () => Promise<void>;
  createSession: () => Promise<Session>;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => Promise<void>;
  searchSessions: (query: string) => Promise<void>;
}
```

#### 3.3 会话API

```
GET    /api/v1/sessions              - 获取会话列表
POST   /api/v1/sessions              - 创建新会话
GET    /api/v1/sessions/{session_id} - 获取会话详情
PATCH  /api/v1/sessions/{session_id} - 更新会话
DELETE /api/v1/sessions/{session_id} - 删除会话
```

### 4. 设置页面（数据源与知识管理）

#### 4.1 全屏设置页面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  设置                                              [×] 关闭      │
├────────────┬────────────────────────────────────────────────────┤
│            │                                                    │
│  📊 数据源 │  数据源管理 / 知识管理                              │
│            │  ─────────────────────────────────────────────────│
│  📚 知识   │                                                    │
│            │  [内容区域]                                         │
│            │                                                    │
│            │                                                    │
│            │                                                    │
│            │                                                    │
│            │                                                    │
└────────────┴────────────────────────────────────────────────────┘
```

#### 4.2 侧滑面板（添加/编辑）

```
┌────────────┬─────────────────────────────────────────┬──────────┐
│            │                                         │          │
│  📊 数据源 │  主内容区域（变暗）                      │ 侧滑面板 │
│            │                                         │          │
│  📚 知识   │                                         │ [表单]   │
│            │                                         │          │
└────────────┴─────────────────────────────────────────┴──────────┘
```

### 5. 数据源管理

#### 5.1 数据源列表

```
┌────────────────────────────────────────────────────────────────┐
│ Prometheus                      🟢 已连接    [编辑] [删除]      │
│ http://prometheus:9090                                         │
│ 最后检测: 2分钟前                                              │
├────────────────────────────────────────────────────────────────┤
│ Loki                            🟢 已连接    [编辑] [删除]      │
│ http://loki:3100                                               │
├────────────────────────────────────────────────────────────────┤
│ InfluxDB                        🔴 连接失败  [编辑] [删除]      │
│ http://influxdb:8086                                           │
│ 错误: Connection refused                                       │
├────────────────────────────────────────────────────────────────┤
│ Jaeger                           🟡 未配置   [配置]            │
└────────────────────────────────────────────────────────────────┘
```

#### 5.2 数据结构

```typescript
interface DataSource {
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
```

#### 5.3 数据源API

```
GET    /api/v1/datasources              - 获取数据源列表
POST   /api/v1/datasources              - 创建数据源
PUT    /api/v1/datasources/{ds_id}      - 更新数据源
DELETE /api/v1/datasources/{ds_id}      - 删除数据源
POST   /api/v1/datasources/{ds_id}/test - 测试连接
POST   /api/v1/datasources/{ds_id}/query - 查询数据
```

### 6. 知识管理

#### 6.1 知识列表

```
┌────────────────────────────────────────────────────────────────┐
│ 🔍 搜索知识...  [全部类型▼]  ➕添加  📤上传                    │
├────────────────────────────────────────────────────────────────┤
│ 📝 API故障排查指南                                             │
│ 类型: 文档  标签: API, 故障, 排查                              │
│ 更新: 2026-03-20  引用: 12次                     [编辑] [删除] │
├────────────────────────────────────────────────────────────────┤
│ 📝 数据库性能优化                                              │
│ 类型: 文档  标签: 数据库, 性能, MySQL                          │
│ 更新: 2026-03-18  引用: 8次                      [编辑] [删除] │
├────────────────────────────────────────────────────────────────┤
│ 📄 Prometheus查询最佳实践.pdf                                  │
│ 类型: 文件  标签: Prometheus, 监控                             │
│ 更新: 2026-03-15  引用: 5次                      [编辑] [删除] │
└────────────────────────────────────────────────────────────────┘
```

#### 6.2 数据结构

```typescript
interface Knowledge {
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
```

#### 6.3 知识API

```
GET    /api/v1/knowledge              - 获取知识列表
POST   /api/v1/knowledge              - 创建知识条目
POST   /api/v1/knowledge/upload       - 上传文档
GET    /api/v1/knowledge/{id}         - 获取知识详情
PUT    /api/v1/knowledge/{id}         - 更新知识
DELETE /api/v1/knowledge/{id}         - 删除知识
GET    /api/v1/knowledge/tags         - 获取标签列表
```

## 数据模型

### 后端数据库模型

```python
# 数据源配置模型
class DataSourceDB(Base):
    __tablename__ = "datasources"
    
    id = Column(String, primary_key=True)
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

# 知识模型
class KnowledgeDB(Base):
    __tablename__ = "knowledge"
    
    id = Column(String, primary_key=True)
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

# Agent执行记录模型
class AgentExecutionDB(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True)
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

## 文件结构

### 后端新增文件

```
backend/
├── app/
│   ├── api/
│   │   ├── websocket.py        # 新增：WebSocket处理
│   │   ├── datasources.py      # 新增：数据源管理API
│   │   └── knowledge.py        # 修改：扩展知识管理API
│   │
│   ├── models/
│   │   ├── datasource.py       # 新增：数据源模型
│   │   ├── agent.py            # 新增：Agent执行模型
│   │   └── knowledge.py        # 新增：知识模型
│   │
│   ├── services/
│   │   ├── datasource_manager.py  # 新增：数据源管理服务
│   │   ├── document_parser.py     # 新增：文档解析服务
│   │   └── connection_tester.py   # 新增：连接测试服务
│   │
│   ├── storage/
│   │   └── repositories/
│   │       ├── datasource_repo.py # 新增：数据源仓库
│   │       └── agent_exec_repo.py # 新增：Agent执行仓库
│   │
│   └── agents/
│       ├── base.py             # 修改：添加AgentIdentity
│       └── orchestrator.py     # 修改：支持流式输出Agent事件
```

### 前端新增文件

```
frontend/
├── src/
│   ├── components/
│   │   ├── Agent/
│   │   │   ├── AgentProcessPanel.tsx
│   │   │   ├── AgentCard.tsx
│   │   │   ├── ThinkingStream.tsx
│   │   │   ├── ToolCallItem.tsx
│   │   │   └── HandoffIndicator.tsx
│   │   │
│   │   ├── Timeline/
│   │   │   ├── VerticalTimeline.tsx
│   │   │   └── TimelineNode.tsx
│   │   │
│   │   ├── Session/
│   │   │   ├── SessionSidebar.tsx
│   │   │   ├── SessionList.tsx
│   │   │   └── SessionToolbar.tsx
│   │   │
│   │   └── Settings/
│   │       ├── SettingsPage.tsx
│   │       ├── SettingsSidebar.tsx
│   │       ├── DataSourceList.tsx
│   │       ├── DataSourceForm.tsx
│   │       ├── KnowledgeList.tsx
│   │       ├── KnowledgeForm.tsx
│   │       └── SlidePanel.tsx
│   │
│   ├── services/
│   │   ├── websocket.ts
│   │   ├── datasourceApi.ts
│   │   └── knowledgeApi.ts
│   │
│   ├── stores/
│   │   ├── agentStore.ts
│   │   └── settingsStore.ts
│   │
│   └── types/
│       ├── agent.ts
│       ├── datasource.ts
│       └── knowledge.ts
```

## 错误处理

### WebSocket连接错误

- 自动重连机制（最多3次，间隔递增）
- 连接状态提示（连接中、已断开、重连中）
- 断线期间的消息缓存

### 数据源连接错误

- 连接测试失败时显示具体错误信息
- 支持重试机制
- 错误状态持久化

### 文档解析错误

- 不支持的文件类型提示
- 解析失败时保留原文
- 大文件上传限制（50MB）

## 安全考虑

### 认证配置加密

- 数据源认证信息加密存储
- 前端不暴露敏感配置
- API返回时脱敏处理

### WebSocket认证

- 基于Session ID的连接验证
- 防止跨会话消息泄露

### 文件上传安全

- 文件类型白名单验证
- 文件大小限制
- 病毒扫描（可选）

## 测试策略

### 单元测试

- WebSocket消息解析
- Agent事件处理
- 数据源连接测试逻辑
- 文档解析逻辑

### 集成测试

- WebSocket端到端通信
- 数据源CRUD流程
- 知识CRUD流程
- 会话管理流程

### E2E测试

- 完整对话流程
- 会话切换流程
- 设置页面操作流程
