# NyxAI - 多Agent协作运维智能体设计文档

## 1. 概述

### 1.1 项目目标

构建一个多Agent协作的运维智能体系统，核心能力包括：
- **故障自愈**：以故障发现、根因分析和自动恢复为核心
- **可信推理**：根因定界需要可信，推理有依据，生成证据链报告
- **知识管理**：支持应用元数据、故障案例库、运维知识库的管理
- **多触发方式**：支持人机对话与机机事件触发对话

### 1.2 核心原则

1. **证据驱动**：所有推理结论必须有证据支撑
2. **半自动执行**：预定义安全操作可自动执行，其他需人工确认
3. **知识增强**：每个Agent可加载相应领域的知识
4. **可追溯性**：完整的证据链和推理报告

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端层 (React + Ant Design)                   │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────────┐  │
│  │  Agent对话界面 │  │ 证据链可视化   │  │    知识管理界面         │  │
│  │  - 流式响应   │  │ - 时间线视图   │  │ - 应用元数据管理        │  │
│  │  - 多会话管理 │  │ - 因果关系图   │  │ - 故障案例库            │  │
│  │  - 操作确认   │  │ - 报告导出     │  │ - 运维知识库            │  │
│  └───────────────┘  └───────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │ WebSocket / REST API
┌─────────────────────────────────────────────────────────────────────┐
│                      后端服务层 (FastAPI + PydanticAI)               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Agent                          │  │
│  │  - 接收事件/对话请求                                           │  │
│  │  - 任务分解与Agent调度                                         │  │
│  │  - 会话状态管理                                                │  │
│  │  - 结果汇总与报告生成                                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         │              │              │                              │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼─────┐                       │
│  │ 调查Agent   │ │根因定界Agent│ │ 恢复Agent │                       │
│  │             │ │             │ │           │                       │
│  │ - 指标查询  │ │ - 证据收集  │ │ - 方案生成│                       │
│  │ - 日志分析  │ │ - 因果推理  │ │ - 安全检查│                       │
│  │ - 链路追踪  │ │ - 置信度评估│ │ - 执行操作│                       │
│  │ - 异常检测  │ │ - 报告生成  │ │ - 回滚支持│                       │
│  └─────────────┘ └────────────┘ └───────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                         工具 & 数据层                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      观测数据工具                              │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │  │
│  │  │Prometheus │  │ InfluxDB  │  │ Loki/ELK  │  │  Jaeger   │  │  │
│  │  │ 指标查询  │  │ 时序数据  │  │ 日志查询  │  │ 链路追踪  │  │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      存储层                                    │  │
│  │  ┌───────────────────────────┐  ┌─────────────────────────┐  │  │
│  │  │   PostgreSQL / SQLite     │  │        Chroma           │  │  │
│  │  │ - 会话记录                │  │  - 应用知识向量         │  │  │
│  │  │ - 证据链                  │  │  - 故障案例向量         │  │  │
│  │  │ - 推理报告                │  │  - 运维知识向量         │  │  │
│  │  │ - 操作记录                │  │  - 语义检索支持         │  │  │
│  │  └───────────────────────────┘  └─────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      LLM层 (多模型支持)                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────────────────┐  │  │
│  │  │ OpenAI  │  │ Claude  │  │ 开源模型 (Qwen/GLM/DeepSeek)│  │  │
│  │  └─────────┘  └─────────┘  └─────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | React + Ant Design | 企业级UI组件库 |
| 后端 | Python + FastAPI | 高性能异步API框架 |
| Agent框架 | PydanticAI | 轻量级Agent框架，代码即配置 |
| 关系数据库 | PostgreSQL (生产) / SQLite (开发) | 结构化数据存储 |
| 向量数据库 | Chroma | 知识向量存储与检索 |
| 包管理 | uv (后端) / pnpm (前端) | 快速依赖管理 |

### 2.3 观测数据源

- **Prometheus**：指标监控
- **InfluxDB**：时序数据
- **Loki/ELK**：日志系统
- **Jaeger**：链路追踪

### 2.4 LLM支持

支持多模型配置切换：
- OpenAI (GPT-4o/GPT-4-turbo)
- Anthropic Claude (Claude 3.5 Sonnet/Opus)
- 开源模型 (Qwen/GLM/DeepSeek)

## 3. Agent协作流程

### 3.1 故障处理流程

```
事件触发/用户提问
        │
        ▼
┌───────────────────┐
│ Orchestrator      │
│ 解析意图，创建会话 │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────┐
│ 阶段1: 调查（调查Agent - 加载观测知识）                            │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 知识增强:                                                    │   │
│ │   - 指标含义解释                                             │   │
│ │   - 日志模式识别规则                                         │   │
│ │   - 应用架构拓扑                                             │   │
│ │                                                              │   │
│ │ 输入: 告警信息/用户描述                                       │   │
│ │ 输出: InvestigationResult                                    │   │
│ │       - anomalies: List[Anomaly] 异常点列表                  │   │
│ │       - evidence: List[Evidence] 原始证据                    │   │
│ │       - data_sources: List[DataSource] 数据来源              │   │
│ │                                                              │   │
│ │ 工具调用:                                                    │   │
│ │   1. query_prometheus() → 指标异常                           │   │
│ │   2. query_influxdb() → 时序数据                             │   │
│ │   3. query_loki() → 相关日志                                 │   │
│ │   4. query_jaeger() → 链路追踪                               │   │
│ └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────┐
│ 阶段2: 根因定界（根因定界Agent - 加载诊断知识）                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 知识增强:                                                    │   │
│ │   - 故障模式库                                               │   │
│ │   - 因果推理规则                                             │   │
│ │   - 历史相似案例                                             │   │
│ │                                                              │   │
│ │ 输入: InvestigationResult                                    │   │
│ │ 输出: RootCauseAnalysis                                      │   │
│ │       - root_cause: str 根因描述                             │   │
│ │       - confidence: float 置信度(0-1)                        │   │
│ │       - evidence_chain: List[EvidenceNode] 证据链            │   │
│ │       - affected_components: List[Component] 影响范围        │   │
│ │       - reasoning_report: str 推理报告                       │   │
│ └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────┐
│ 阶段3: 恢复（恢复Agent - 加载恢复知识）                             │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 知识增强:                                                    │   │
│ │   - 恢复操作手册                                             │   │
│ │   - 安全操作规范                                             │   │
│ │   - 历史恢复案例                                             │   │
│ │   - 应用配置信息                                             │   │
│ │                                                              │   │
│ │ 输入: RootCauseAnalysis                                      │   │
│ │ 输出: RecoveryPlan                                           │   │
│ │       - actions: List[RecoveryAction] 恢复操作列表           │   │
│ │       - risk_level: Enum[low, medium, high] 风险等级         │   │
│ │       - requires_confirmation: bool 是否需要确认             │   │
│ │       - rollback_plan: RollbackPlan 回滚方案                 │   │
│ └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────┐
│ 阶段4: 执行与验证                                                   │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 半自动执行流程:                                              │   │
│ │   1. 风险评估 → 低风险自动执行，中高风险需确认               │   │
│ │   2. 用户确认 → 展示证据链和推理报告，等待确认               │   │
│ │   3. 执行操作 → 记录每步执行结果                             │   │
│ │   4. 效果验证 → 检查指标是否恢复                             │   │
│ │   5. 自动回滚 → 验证失败时执行回滚                           │   │
│ └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────┐
│ 阶段5: 归档与学习                                                   │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ - 生成完整推理报告（含证据链图）                              │   │
│ │ - 存储到PostgreSQL（结构化）和Chroma（向量）                  │   │
│ │ - 更新知识库，形成新案例                                      │   │
│ └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### 3.2 知识注入机制

每个Agent可加载特定领域的知识：

```python
class AgentKnowledge:
    investigation_knowledge = [
        "metric_definitions",      # 指标定义
        "log_patterns",            # 日志模式
        "application_topology",    # 应用拓扑
        "alert_rules",             # 告警规则
    ]
    
    diagnosis_knowledge = [
        "fault_patterns",          # 故障模式
        "causal_rules",            # 因果规则
        "historical_cases",        # 历史案例
        "component_dependencies",  # 组件依赖
    ]
    
    recovery_knowledge = [
        "recovery_playbooks",      # 恢复手册
        "safety_guidelines",       # 安全规范
        "rollback_procedures",     # 回滚流程
        "application_configs",     # 应用配置
    ]
```

## 4. 核心数据模型

### 4.1 证据模型

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EvidenceType(str, Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    KNOWLEDGE = "knowledge"

class Evidence(BaseModel):
    id: str = Field(..., description="证据唯一标识")
    evidence_type: EvidenceType
    description: str = Field(..., description="证据描述")
    source_data: Dict[str, Any] = Field(..., description="原始数据")
    source_system: str = Field(..., description="来源系统")
    timestamp: datetime
    confidence: float = Field(..., ge=0, le=1, description="证据可信度")

class EvidenceNode(BaseModel):
    id: str
    description: str
    evidence: Evidence
    supports: List[str] = Field(default_factory=list, description="支持的证据节点ID")
    contradicts: List[str] = Field(default_factory=list, description="反驳的证据节点ID")
    inference_step: str = Field(..., description="推理步骤说明")
```

### 4.2 会话模型

```python
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
    component: str = Field(..., description="异常组件")
    anomaly_type: str = Field(..., description="异常类型")
    severity: str = Field(..., description="严重程度")
    evidence_ids: List[str] = Field(..., description="关联证据")
    detected_at: datetime

class InvestigationResult(BaseModel):
    session_id: str
    anomalies: List[Anomaly]
    evidence: List[Evidence]
    summary: str = Field(..., description="调查摘要")
    created_at: datetime

class RootCauseAnalysis(BaseModel):
    session_id: str
    root_cause: str = Field(..., description="根因描述")
    confidence: float = Field(..., ge=0, le=1)
    evidence_chain: List[EvidenceNode] = Field(..., description="证据链")
    affected_components: List[str]
    reasoning_report: str = Field(..., description="推理报告")
    similar_cases: List[str] = Field(default_factory=list, description="相似案例ID")
    created_at: datetime

class RecoveryAction(BaseModel):
    id: str
    action_type: str
    target: str
    params: Dict[str, Any]
    description: str
    risk_level: RiskLevel
    evidence_based: bool = Field(..., description="是否基于证据")
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
    trigger_type: str = Field(..., description="触发类型: webhook/scheduled/chat")
    trigger_source: str = Field(..., description="触发来源")
    status: SessionStatus
    investigation: Optional[InvestigationResult]
    root_cause: Optional[RootCauseAnalysis]
    recovery_plan: Optional[RecoveryPlan]
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

## 5. API接口设计

### 5.1 REST API

```
会话管理
├── POST   /api/v1/sessions                    创建会话（手动触发）
├── GET    /api/v1/sessions                    获取会话列表
├── GET    /api/v1/sessions/{session_id}       获取会话详情
└── DELETE /api/v1/sessions/{session_id}       删除会话

对话接口
├── POST   /api/v1/chat/message                发送消息（非流式）
└── POST   /api/v1/chat/stream                 发送消息（流式SSE）

证据与报告
├── GET    /api/v1/sessions/{session_id}/evidence      获取证据链
├── GET    /api/v1/sessions/{session_id}/report        获取推理报告
└── GET    /api/v1/sessions/{session_id}/report/export 导出报告

恢复操作
├── POST   /api/v1/sessions/{session_id}/actions/confirm  确认执行操作
├── POST   /api/v1/sessions/{session_id}/actions/execute  执行操作
└── POST   /api/v1/sessions/{session_id}/actions/rollback 回滚操作

知识管理
├── GET    /api/v1/knowledge/apps              获取应用列表
├── POST   /api/v1/knowledge/apps              添加应用元数据
├── GET    /api/v1/knowledge/cases             获取故障案例列表
├── POST   /api/v1/knowledge/cases             添加故障案例
├── GET    /api/v1/knowledge/docs              获取知识文档列表
└── POST   /api/v1/knowledge/docs              添加知识文档

事件入口
├── POST   /webhook/alert                      接收告警Webhook
└── POST   /webhook/custom                     接收自定义Webhook
```

### 5.2 WebSocket

```
/ws/chat                                         实时对话
├── 发送消息: {"type": "message", "content": "..."}
└── 接收消息: {"type": "response", "content": "...", "done": false}

/ws/sessions/{session_id}                        会话状态推送
└── 接收: {"type": "status_update", "status": "investigating", "progress": 30}
```

## 6. 前端界面设计

### 6.1 主界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  NyxAI - 运维智能体                              [用户] [设置] [帮助] │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ ┌───────────────────────┐ ┌───────────────────────────────────────┐ │
│ │ 会话列表              │ │ 主对话区                              │ │
│ │ ───────────────────── │ │ ───────────────────────────────────── │ │
│ │ 🔴 [进行中] 数据库延迟 │ │ [Agent] 收到告警：数据库响应延迟超过   │ │
│ │ 🟢 [已完成] API超时   │ │        5秒，正在调查...               │ │
│ │ 🟢 [已完成] 内存泄漏  │ │                                       │ │
│ │                       │ │ ┌───────────────────────────────────┐ │ │
│ │ ───────────────────── │ │ │ 📊 调查进度                       │ │ │
│ │ + 新建会话            │ │ │ ├─ 指标分析 ✓                     │ │ │
│ │                       │ │ │ ├─ 日志检索 ✓                     │ │ │
│ │ ───────────────────── │ │ │ └─ 链路追踪 ⏳                    │ │ │
│ │ 📚 知识管理           │ │ └───────────────────────────────────┘ │ │
│ │   ├─ 应用管理         │ │                                       │ │
│ │   ├─ 故障案例         │ │ [Agent] 发现异常：                    │ │
│ │   └─ 运维文档         │ │        MySQL主库CPU使用率突增至95%    │ │
│ │                       │ │        相关慢查询日志增加10倍         │ │
│ │ ───────────────────── │ │                                       │ │
│ │ ⚙️ 系统设置           │ │ ┌───────────────────────────────────┐ │ │
│ │                       │ │ │ 🔍 根因分析                       │ │ │
│ └───────────────────────┘ │ │ 置信度: 85%                       │ │ │
│                           │ │ 根因: 慢查询导致CPU过载            │ │ │
│                           │ │ └───────────────────────────────────┘ │ │
│                           │ │                                       │ │
│                           │ │ ┌───────────────────────────────────┐ │ │
│                           │ │ │ 🔧 恢复方案                       │ │ │
│                           │ │ │ 风险: 中                          │ │ │
│                           │ │ │ [查看证据链] [确认执行] [拒绝]    │ │ │
│                           │ │ └───────────────────────────────────┘ │ │
│                           │ │                                       │ │
│                           │ └───────────────────────────────────────┘ │
│                           │ ┌───────────────────────────────────────┐ │
│                           │ │ 输入消息...              [发送]       │ │
│                           │ └───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 证据链视图

```
时间线视图:
─────────────────────────────────────────────────────────────────────→
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐        ┌─────────────┐      ┌─────────────┐
│ 指标证据 │───────▶│ 日志证据     │─────▶│ 链路证据     │
│ CPU 95% │        │ 慢查询增加   │      │ 查询耗时5s+ │
└─────────┘        └─────────────┘      └─────────────┘
    │                    │                    │
    └────────────────────┴────────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ 根因结论     │
                   │ 慢查询过载   │
                   │ 置信度: 85% │
                   └─────────────┘

因果关系图:
                    ┌─────────────┐
                    │ CPU使用率高  │
                    └──────┬──────┘
                           │ 导致
                           ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ 查询响应慢   │◀──│ 慢查询堆积   │──▶│ 连接池耗尽   │
    └─────────────┘   └─────────────┘   └─────────────┘
         │                                     │
         └──────────────────┬──────────────────┘
                            │ 表现为
                            ▼
                     ┌─────────────┐
                     │ API超时告警  │
                     └─────────────┘
```

## 7. 项目目录结构

```
NyxAI/
├── backend/                          # Python后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI入口
│   │   ├── config.py                 # 配置管理
│   │   ├── dependencies.py           # 依赖注入
│   │   │
│   │   ├── agents/                   # Agent模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Agent基类
│   │   │   ├── orchestrator.py       # 编排Agent
│   │   │   ├── investigation.py      # 调查Agent
│   │   │   ├── diagnosis.py          # 根因定界Agent
│   │   │   └── recovery.py           # 恢复Agent
│   │   │
│   │   ├── tools/                    # 工具模块
│   │   │   ├── __init__.py
│   │   │   ├── prometheus.py         # Prometheus工具
│   │   │   ├── influxdb.py           # InfluxDB工具
│   │   │   ├── loki.py               # Loki日志工具
│   │   │   ├── jaeger.py             # Jaeger链路工具
│   │   │   └── knowledge.py          # 知识检索工具
│   │   │
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── session.py            # 会话模型
│   │   │   ├── evidence.py           # 证据模型
│   │   │   ├── knowledge.py          # 知识模型
│   │   │   └── api.py                # API请求/响应模型
│   │   │
│   │   ├── api/                      # API路由
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py           # 会话API
│   │   │   ├── chat.py               # 对话API
│   │   │   ├── knowledge.py          # 知识管理API
│   │   │   └── webhook.py            # Webhook入口
│   │   │
│   │   ├── services/                 # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── llm.py                # LLM服务（多模型）
│   │   │   ├── vector_store.py       # 向量存储服务
│   │   │   └── scheduler.py          # 定时任务服务
│   │   │
│   │   ├── storage/                  # 存储层
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # 数据库连接
│   │   │   └── repositories/         # 数据仓库
│   │   │       ├── session.py
│   │   │       ├── evidence.py
│   │   │       └── knowledge.py
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       └── logger.py
│   │
│   ├── tests/                        # 测试
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   ├── test_tools/
│   │   └── test_api/
│   │
│   ├── alembic/                      # 数据库迁移
│   │   └── versions/
│   │
│   ├── pyproject.toml                # 项目配置
│   ├── uv.lock                       # uv依赖锁定
│   └── alembic.ini
│
├── frontend/                         # React前端
│   ├── src/
│   │   ├── components/               # 组件
│   │   │   ├── Chat/                 # 对话组件
│   │   │   ├── EvidenceChain/        # 证据链组件
│   │   │   ├── Knowledge/            # 知识管理组件
│   │   │   └── Layout/               # 布局组件
│   │   │
│   │   ├── pages/                    # 页面
│   │   │   ├── Home/                 # 主页
│   │   │   ├── Session/              # 会话详情
│   │   │   └── Knowledge/            # 知识管理
│   │   │
│   │   ├── services/                 # API服务
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   │
│   │   ├── stores/                   # 状态管理
│   │   │   └── sessionStore.ts
│   │   │
│   │   ├── types/                    # 类型定义
│   │   │   └── index.ts
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docs/                             # 文档
│   └── superpowers/
│       └── specs/
│
├── docker-compose.yml                # 开发环境
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

## 8. 非功能性需求

### 8.1 性能要求

- 对话响应延迟 < 2秒（首字节）
- 证据链查询 < 500ms
- 支持100并发会话

### 8.2 可靠性要求

- 会话状态持久化，支持断点续传
- 操作执行支持幂等性
- 支持操作回滚

### 8.3 安全要求

- 敏感操作二次确认
- 操作审计日志

## 9. 开发计划建议

### Phase 1: 核心框架（2周）
- 项目骨架搭建
- Agent基类和编排器
- 基础API框架
- 数据库模型和迁移

### Phase 2: Agent实现（3周）
- 调查Agent + 观测工具
- 根因定界Agent + 证据链
- 恢复Agent + 安全检查

### Phase 3: 知识系统（2周）
- Chroma向量存储集成
- 知识注入机制
- 知识管理API

### Phase 4: 前端界面（3周）
- 对话界面
- 证据链可视化
- 知识管理界面

### Phase 5: 集成测试（1周）
- 端到端测试
- 性能优化
- 文档完善
