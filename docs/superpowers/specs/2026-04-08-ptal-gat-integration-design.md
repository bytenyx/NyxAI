# NyxAI PTAL-GAT 故障预测系统集成设计文档

## 文档信息

- **创建日期**: 2026-04-08
- **版本**: v1.0
- **作者**: AI Assistant
- **状态**: 待审核

## 1. 概述

### 1.1 项目背景

NyxAI 是一个基于多 Agent 协作的运维智能体系统，支持自主调查观测数据、根因定界、故障恢复，并生成证据链报告。当前系统采用反应式模式，即在故障发生后进行诊断和恢复。

PTAL-GAT（Physical Theory Anchored Learning with Graph Attention Networks）是一个基于物理先验锚定的图注意力网络模型，用于 OpenResty 三级全球分布式 API 网关的故障预测与异常检测。该系统采用预测式模式，能够在故障发生前 15-60 分钟进行预警。

### 1.2 集成目标

将 PTAL-GAT 故障预测系统深度集成到现有 NyxAI 系统中，形成"预测 → 诊断 → 恢复"的完整闭环，实现：

1. **预测式故障预警**：提前 15-60 分钟预警潜在故障
2. **主动式运维**：从被动响应转向主动预防
3. **统一架构**：预测、诊断、恢复三大能力深度融合
4. **完整闭环**：预测结果驱动诊断，诊断结果反馈优化预测模型

### 1.3 核心价值

| 维度 | 现有 NyxAI | 集成后 NyxAI | 价值提升 |
|------|-----------|-------------|---------|
| **能力模式** | 反应式 | 预测式 + 反应式 | 从被动到主动 |
| **预警窗口** | 无 | 15-60 分钟 | 提前预警 |
| **异常检测** | 基于规则 | 基于模型（F1≥95%） | 精度提升 |
| **根因定位** | Top-3 准确率 ~85% | Top-3 准确率 ≥92% | 准确率提升 7% |
| **告警收敛** | 无 | 收敛率 ≥85% | 减少告警风暴 |
| **MTTR** | 基准 | 缩短 60% | 恢复效率提升 |

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    NyxAI 增强版 - 整体架构                        │
│              （预测 + 诊断 + 恢复 完整闭环）                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    前端层（React + Ant Design）                  │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ 对话界面      │  │ 拓扑可视化    │  │ 告警管理         │    │
│  │ (ChatWindow)  │  │ (Topology)    │  │ (AlertPanel)     │    │
│  └───────────────┘  └───────────────┘  └──────────────────┘    │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ 证据链可视化  │  │ 模型性能监控  │  │ 指标大屏         │    │
│  │ (Evidence)    │  │ (ModelPerf)   │  │ (Metrics)        │    │
│  └───────────────┘  └───────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket / REST API
┌─────────────────────────────────────────────────────────────────┐
│                    API 层 (FastAPI)                             │
│  ├─ /api/v1/chat/*           → 对话接口                        │
│  ├─ /api/v1/sessions/*       → 会话管理                        │
│  ├─ /api/v1/prediction/*     → 预测接口（新增）                │
│  ├─ /api/v1/topology/*       → 拓扑管理（新增）                │
│  ├─ /api/v1/alerts/*         → 告警管理（新增）                │
│  ├─ /api/v1/knowledge/*      → 知识管理                        │
│  └─ /webhook/*               → 事件入口                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Agent 编排层（核心）                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Orchestrator Agent                     │   │
│  │  - 接收事件/对话请求                                      │   │
│  │  - 任务分解与 Agent 调度                                  │   │
│  │  - 协调预测、诊断、恢复流程                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │              │              │              │           │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐   │
│  │ Prediction  │ │Investigate │ │ Diagnose  │ │ Recovery  │   │
│  │ Agent       │ │ Agent      │ │ Agent     │ │ Agent     │   │
│  │ (新增)      │ │            │ │           │ │           │   │
│  │             │ │            │ │           │ │           │   │
│  │ - 拓扑管理  │ │ - 指标查询 │ │ - 证据收集│ │ - 方案生成│   │
│  │ - 模型推理  │ │ - 日志分析 │ │ - 因果推理│ │ - 安全检查│   │
│  │ - 异常检测  │ │ - 链路追踪 │ │ - 根因定位│ │ - 执行操作│   │
│  │ - 预测告警  │ │ - 异常检测 │ │ - 报告生成│ │ - 回滚支持│   │
│  └─────────────┘ └────────────┘ └───────────┘ └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    服务层（业务逻辑）                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 预测服务（新增）                                          │   │
│  │ ├─ TopologyService      → 拓扑管理                       │   │
│  │ ├─ DataPreprocessService → 数据预处理                     │   │
│  │ ├─ ModelTrainingService  → 模型训练（PTAL-GAT）          │   │
│  │ ├─ ModelInferenceService → 模型推理                      │   │
│  │ └─ AnomalyAnalysisService → 异常分析                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 诊断服务（现有）                                          │   │
│  │ ├─ LLMService           → LLM 调用                       │   │
│  │ └─ VectorStoreService   → 向量检索                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 告警服务（新增）                                          │   │
│  │ ├─ AlertService         → 告警生成与收敛                 │   │
│  │ └─ NotificationService  → 通知推送                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    工具层（数据访问）                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 观测数据工具                                              │   │
│  │ ├─ PrometheusTool    → 指标查询                          │   │
│  │ ├─ InfluxDBTool      → 时序数据                          │   │
│  │ ├─ LokiTool          → 日志查询                          │   │
│  │ └─ JaegerTool        → 链路追踪                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 拓扑工具（新增）                                          │   │
│  │ ├─ CMDBTool          → CMDB 对接                         │   │
│  │ └─ TopologyTool      → 拓扑查询与更新                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 知识工具                                                  │   │
│  │ └─ KnowledgeTool     → 知识检索                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    存储层（统一）                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ InfluxDB 1.x  │  │ Neo4j         │  │ Elasticsearch    │    │
│  │ (时序数据)    │  │ (拓扑数据)    │  │ (日志数据)       │    │
│  └───────────────┘  └───────────────┘  └──────────────────┘    │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ PostgreSQL    │  │ Chroma        │  │ MLflow           │    │
│  │ (结构化数据)  │  │ (向量数据)    │  │ (模型管理)       │    │
│  └───────────────┘  └───────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    数据采集层（统一）                             │
│  ├─ node-exporter           → 虚拟机性能指标                   │
│  ├─ nginx-lua-prometheus    → 网关业务指标                     │
│  ├─ filebeat                → 访问日志                         │
│  └─ 现有采集组件（Prometheus + InfluxDB + Loki + Jaeger）       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计理念

1. **统一架构**：预测、诊断、恢复三大能力深度融合
2. **Agent 协作**：Prediction Agent 作为新的核心 Agent
3. **数据统一**：统一存储层，避免数据孤岛
4. **Docker 部署**：所有组件容器化，统一管理

## 3. Agent 协作流程设计

### 3.1 预测驱动的主动运维流程

```
定时预测触发（每30秒）
        │
        ▼
┌───────────────────┐
│ Orchestrator      │
│ 解析预测任务       │
└─────────┬─────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段1: 预测（Prediction Agent - 新增）                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 知识增强:                                                    │ │
│ │   - 网关拓扑结构                                             │ │
│ │   - 历史故障模式                                             │ │
│ │   - PTAL-GAT 模型参数                                        │ │
│ │                                                              │ │
│ │ 工具调用:                                                    │ │
│ │   1. query_influxdb() → 获取最新指标数据                     │ │
│ │   2. get_topology() → 获取当前拓扑                           │ │
│ │   3. preprocess_data() → 数据预处理                          │ │
│ │   4. model_inference() → PTAL-GAT 推理                       │ │
│ │   5. analyze_anomalies() → 异常分析                          │ │
│ │                                                              │ │
│ │ 输出: PredictionResult                                       │ │
│ │       - anomaly_scores: List[AnomalyScore] 异常分数          │ │
│ │       - cascade_risk: float 级联故障风险                     │ │
│ │       - root_cause_candidates: List[Node] 根因候选           │ │
│ │       - prediction_window: int 预警窗口（分钟）              │ │
│ │       - confidence: float 置信度                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          │ 是否检测到异常？
          │
          ├─ 否 ──→ 记录正常状态，继续监控
          │
          └─ 是
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段2: 告警生成与收敛                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ AlertService:                                               │ │
│ │   1. 生成预测告警                                           │ │
│ │   2. 基于拓扑收敛关联告警                                   │ │
│ │   3. 推送至运维人员                                         │ │
│ │   4. 触发诊断流程                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段3: 调查（Investigation Agent - 现有）                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 输入: PredictionResult                                      │ │
│ │                                                              │ │
│ │ 工具调用:                                                    │ │
│ │   1. query_prometheus() → 详细指标分析                      │ │
│ │   2. query_loki() → 相关日志检索                            │ │
│ │   3. query_jaeger() → 链路追踪                              │ │
│ │                                                              │ │
│ │ 输出: InvestigationResult                                    │ │
│ │       - anomalies: List[Anomaly] 详细异常列表                │ │
│ │       - evidence: List[Evidence] 证据                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段4: 根因定界（Diagnosis Agent - 现有）                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 输入: InvestigationResult + PredictionResult                │ │
│ │                                                              │ │
│ │ 知识增强:                                                    │ │
│ │   - 故障模式库                                               │ │
│ │   - 因果推理规则                                             │ │
│ │   - 历史相似案例                                             │ │
│ │                                                              │ │
│ │ 输出: RootCauseAnalysis                                      │ │
│ │       - root_cause: str 根因描述                             │ │
│ │       - confidence: float 置信度                             │ │
│ │       - evidence_chain: List[EvidenceNode] 证据链            │ │
│ │       - affected_components: List[Component] 影响范围        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段5: 恢复（Recovery Agent - 现有）                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 输入: RootCauseAnalysis                                      │ │
│ │                                                              │ │
│ │ 输出: RecoveryPlan                                           │ │
│ │       - actions: List[RecoveryAction] 恢复操作列表           │ │
│ │       - risk_level: Enum[low, medium, high] 风险等级         │ │
│ │       - requires_confirmation: bool 是否需要确认             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段6: 执行与验证                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 半自动执行流程:                                              │ │
│ │   1. 风险评估 → 低风险自动执行，中高风险需确认               │ │
│ │   2. 用户确认 → 展示证据链和推理报告                         │ │
│ │   3. 执行操作 → 记录每步执行结果                             │ │
│ │   4. 效果验证 → 检查指标是否恢复                             │ │
│ │   5. 自动回滚 → 验证失败时执行回滚                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段7: 闭环优化                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ - 反馈处置结果至 PTAL-GAT 模型                               │ │
│ │ - 优化模型异常阈值                                           │ │
│ │ - 更新知识库，形成新案例                                     │ │
│ │ - 生成完整报告                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 告警触发的被动诊断流程

```
外部告警触发
        │
        ▼
┌───────────────────┐
│ Orchestrator      │
│ 解析告警信息       │
└─────────┬─────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 阶段1: 快速预测（Prediction Agent）                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 基于告警信息快速推理:                                        │ │
│ │   1. 获取相关节点拓扑                                       │ │
│ │   2. 查询最近5分钟指标                                      │ │
│ │   3. 快速推理获取异常分数                                   │ │
│ │   4. 提供根因候选列表                                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
    继续现有诊断流程（Investigation → Diagnosis → Recovery）
```

### 3.3 关键设计点

1. **Prediction Agent 定位**：
   - 作为新的核心 Agent，负责预测和异常检测
   - 与现有 Investigation、Diagnosis、Recovery Agent 协作
   - 支持主动预测和被动诊断两种场景

2. **协作模式**：
   - **主动模式**：定时预测 → 发现异常 → 触发诊断恢复
   - **被动模式**：外部告警 → 快速预测 → 辅助诊断

3. **数据流转**：
   - Prediction Agent 提供 PredictionResult
   - Investigation Agent 基于预测结果深入调查
   - Diagnosis Agent 结合预测和调查结果进行根因定界

## 4. 核心数据模型设计

### 4.1 预测相关模型（新增）

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    EDGE = "edge"           # 边缘接入层
    CORE = "core"           # 核心转发层
    POP = "pop"             # POP点

class NodeStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    ABNORMAL = "abnormal"
    OFFLINE = "offline"

class TopologyNode(BaseModel):
    id: str = Field(..., description="节点唯一标识")
    ip: str = Field(..., description="节点IP")
    node_type: NodeType
    pop: str = Field(..., description="所属POP点")
    region: str = Field(..., description="所属区域")
    status: NodeStatus = NodeStatus.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict, description="节点元数据")
    created_at: datetime
    updated_at: datetime

class TopologyEdge(BaseModel):
    id: str = Field(..., description="边唯一标识")
    source_node_id: str
    target_node_id: str
    dependency_type: str = Field(..., description="依赖类型: upstream/forward")
    traffic_ratio: float = Field(..., ge=0, le=1, description="流量占比")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class AnomalyScore(BaseModel):
    node_id: str
    score: float = Field(..., ge=0, le=1, description="异常分数")
    anomaly_type: str = Field(..., description="异常类型: performance/config/network")
    confidence: float = Field(..., ge=0, le=1)
    detected_at: datetime
    contributing_features: List[str] = Field(default_factory=list, description="贡献特征")

class PredictionResult(BaseModel):
    session_id: str
    prediction_time: datetime
    prediction_window: int = Field(..., description="预警窗口（分钟）")
    
    anomaly_scores: List[AnomalyScore]
    cascade_risk: float = Field(..., ge=0, le=1, description="级联故障风险")
    root_cause_candidates: List[str] = Field(..., description="根因候选节点ID")
    
    model_version: str = Field(..., description="模型版本")
    inference_latency: float = Field(..., description="推理延迟（ms）")
    confidence: float = Field(..., ge=0, le=1)
    
    created_at: datetime
```

### 4.2 告警相关模型（新增）

```python
class AlertLevel(str, Enum):
    CRITICAL = "critical"   # 紧急：核心节点异常、级联故障
    IMPORTANT = "important" # 重要：区域节点异常
    NORMAL = "normal"       # 一般：边缘节点异常

class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class Alert(BaseModel):
    id: str = Field(..., description="告警唯一标识")
    session_id: Optional[str] = Field(None, description="关联会话ID")
    
    alert_level: AlertLevel
    alert_type: str = Field(..., description="告警类型: prediction/threshold/system")
    status: AlertStatus = AlertStatus.FIRING
    
    title: str
    description: str
    
    affected_nodes: List[str] = Field(default_factory=list)
    root_cause_node: Optional[str] = None
    
    prediction_result: Optional[PredictionResult] = None
    
    # 告警收敛相关
    parent_alert_id: Optional[str] = Field(None, description="父告警ID（收敛关系）")
    related_alert_ids: List[str] = Field(default_factory=list, description="关联告警ID")
    
    # 处置相关
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
```

### 4.3 现有模型增强

```python
class EvidenceType(str, Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    KNOWLEDGE = "knowledge"
    PREDICTION = "prediction"  # 新增：预测证据

class SessionStatus(str, Enum):
    PREDICTING = "predicting"       # 新增：预测中
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"

class Session(BaseModel):
    id: str
    trigger_type: str = Field(..., description="触发类型: prediction/webhook/scheduled/chat")
    trigger_source: str
    
    status: SessionStatus
    
    # 预测结果（新增）
    prediction: Optional[PredictionResult] = None
    
    # 现有字段
    investigation: Optional['InvestigationResult'] = None
    root_cause: Optional['RootCauseAnalysis'] = None
    recovery_plan: Optional['RecoveryPlan'] = None
    
    # 关联告警（新增）
    alerts: List[str] = Field(default_factory=list, description="关联告警ID列表")
    
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

class RootCauseAnalysis(BaseModel):
    session_id: str
    root_cause: str
    confidence: float = Field(..., ge=0, le=1)
    evidence_chain: List[EvidenceNode]
    affected_components: List[str]
    reasoning_report: str
    similar_cases: List[str] = Field(default_factory=list)
    
    # 新增：预测辅助信息
    prediction_assisted: bool = Field(False, description="是否由预测辅助")
    prediction_confidence: Optional[float] = None
    
    created_at: datetime
```

## 5. API 接口设计

### 5.1 预测相关 API（新增）

```
预测管理
├── POST   /api/v1/prediction/execute              执行预测
│   Request: {
│     "node_ids": ["node1", "node2"],  // 可选，不传则全量预测
│     "prediction_window": 30          // 预警窗口（分钟）
│   }
│   Response: PredictionResult
│
├── GET    /api/v1/prediction/history              获取预测历史
│   Query: ?start_time=xxx&end_time=xxx&node_id=xxx
│   Response: List[PredictionResult]
│
└── GET    /api/v1/prediction/{prediction_id}      获取预测详情
    Response: PredictionResult

拓扑管理
├── GET    /api/v1/topology                        获取完整拓扑
│   Response: {
│     "nodes": List[TopologyNode],
│     "edges": List[TopologyEdge],
│     "adjacency_matrix": Dict[str, List[str]]
│   }
│
├── POST   /api/v1/topology/sync                   同步拓扑（从CMDB）
│   Response: {
│     "updated": bool,
│     "changes": {
│       "added_nodes": int,
│       "removed_nodes": int,
│       "updated_nodes": int,
│       "added_edges": int,
│       "removed_edges": int
│     }
│   }
│
├── POST   /api/v1/topology/validate               校验拓扑
│   Response: {
│     "is_valid": bool,
│     "issues": List[str],
│     "consistency_rate": float
│   }
│
├── GET    /api/v1/topology/nodes                  获取节点列表
│   Query: ?node_type=edge&pop=xxx&status=normal
│   Response: List[TopologyNode]
│
├── GET    /api/v1/topology/nodes/{node_id}        获取节点详情
│   Response: TopologyNode
│
└── PUT    /api/v1/topology/nodes/{node_id}        更新节点信息
    Request: TopologyNode
    Response: TopologyNode

模型管理
├── POST   /api/v1/model/train                     触发模型训练
│   Request: {
│     "training_type": "full|incremental",
│     "data_range": {
│       "start_time": "2026-01-01T00:00:00Z",
│       "end_time": "2026-01-14T23:59:59Z"
│     },
│     "hyperparameters": {
│       "learning_rate": 0.001,
│       "epochs": 100
│     }
│   }
│   Response: {
│     "training_id": "train_xxx",
│     "status": "running"
│   }
│
├── GET    /api/v1/model/training/{training_id}    获取训练状态
│   Response: {
│     "training_id": "train_xxx",
│     "status": "running|completed|failed",
│     "progress": 0.75,
│     "metrics": {
│       "loss": 0.05,
│       "val_loss": 0.06
│     },
│     "started_at": "2026-01-15T10:00:00Z",
│     "completed_at": null
│   }
│
├── GET    /api/v1/model/versions                  获取模型版本列表
│   Response: List[{
│     "version": "v1.0.0",
│     "created_at": "2026-01-15T10:00:00Z",
│     "metrics": {
│       "f1_score": 0.96,
│       "precision": 0.95,
│       "recall": 0.97
│     },
│     "is_active": true
│   }]
│
├── POST   /api/v1/model/activate/{version}        激活模型版本
│   Response: {"success": true}
│
└── GET    /api/v1/model/performance               获取模型性能
    Query: ?start_time=xxx&end_time=xxx
    Response: {
      "f1_score": 0.96,
      "precision": 0.95,
      "recall": 0.97,
      "false_positive_rate": 0.03,
      "inference_latency_avg": 85.5,
      "prediction_accuracy": 0.93
    }
```

### 5.2 告警相关 API（新增）

```
告警管理
├── GET    /api/v1/alerts                          获取告警列表
│   Query: ?level=critical&status=firing&start_time=xxx
│   Response: List[Alert]
│
├── GET    /api/v1/alerts/{alert_id}               获取告警详情
│   Response: Alert
│
├── POST   /api/v1/alerts/{alert_id}/acknowledge   确认告警
│   Request: {"acknowledged_by": "user_xxx"}
│   Response: Alert
│
├── POST   /api/v1/alerts/{alert_id}/resolve       解决告警
│   Request: {"resolved_by": "user_xxx", "resolution": "xxx"}
│   Response: Alert
│
├── GET    /api/v1/alerts/statistics               获取告警统计
│   Query: ?start_time=xxx&end_time=xxx
│   Response: {
│     "total": 150,
│     "by_level": {
│       "critical": 10,
│       "important": 40,
│       "normal": 100
│     },
│     "by_status": {
│       "firing": 20,
│       "acknowledged": 30,
│       "resolved": 100
│     },
│     "convergence_rate": 0.87
│   }
│
└── GET    /api/v1/alerts/trends                   获取告警趋势
    Query: ?start_time=xxx&end_time=xxx&interval=1h
    Response: List[{
      "timestamp": "2026-01-15T10:00:00Z",
      "count": 15,
      "by_level": {"critical": 1, "important": 4, "normal": 10}
    }]
```

### 5.3 现有 API 增强

```
会话管理
├── POST   /api/v1/sessions                        创建会话
│   Request: {
│     "trigger_type": "prediction|webhook|chat",
│     "trigger_source": "xxx",
│     "initial_prediction_id": "pred_xxx"  // 新增：关联预测
│   }
│   Response: Session

证据与报告
├── GET    /api/v1/sessions/{session_id}/report    获取推理报告
│   Response: {
│     "session": Session,
│     "prediction": PredictionResult,  // 新增
│     "investigation": InvestigationResult,
│     "root_cause": RootCauseAnalysis,
│     "recovery_plan": RecoveryPlan,
│     "evidence_chain": List[EvidenceNode]
│   }

WebSocket 接口
├── /ws/sessions/{session_id}        会话状态推送
│   └── 接收: {
│         "type": "status_update",
│         "status": "predicting",
│         "progress": 30,
│         "message": "正在执行预测..."
│       }
│
├── /ws/alerts                       告警实时推送
│   └── 接收: {
│         "type": "new_alert",
│         "alert": Alert
│       }
│
└── /ws/topology                     拓扑变更推送
    └── 接收: {
          "type": "topology_update",
          "changes": {...}
        }
```

## 6. Docker 部署架构设计

### 6.1 完整 docker-compose.yml

```yaml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://backend:8000
      - VITE_WS_URL=ws://backend:8000
    depends_on:
      - backend
    networks:
      - nyxai-network
    restart: unless-stopped

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://nyxai:nyxai@postgres:5432/nyxai
      - INFLUXDB_URL=http://influxdb:8086
      - NEO4J_URL=bolt://neo4j:7687
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - CHROMA_URL=http://chroma:8000
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - ./backend/app:/app/app:ro
      - ./backend/skills:/app/skills:ro
    depends_on:
      - postgres
      - influxdb
      - neo4j
      - elasticsearch
      - chroma
      - mlflow
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 数据存储层
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=nyxai
      - POSTGRES_PASSWORD=nyxai
      - POSTGRES_DB=nyxai
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nyxai"]
      interval: 10s
      timeout: 5s
      retries: 5

  influxdb:
    image: influxdb:1.8-alpine
    environment:
      - INFLUXDB_DB=nyxai_metrics
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=admin
    volumes:
      - influxdb-data:/var/lib/influxdb
    ports:
      - "8086:8086"
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  neo4j:
    image: neo4j:5.15-community
    environment:
      - NEO4J_AUTH=neo4j/nyxai123
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 30s
      timeout: 10s
      retries: 3

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      - "9300:9300"
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  chroma:
    image: chromadb/chroma:latest
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    volumes:
      - chroma-data:/chroma/data
    ports:
      - "8001:8000"
    networks:
      - nyxai-network
    restart: unless-stopped

  # 模型管理服务
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.9.2
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://nyxai:nyxai@postgres:5432/mlflow
      - MLFLOW_ARTIFACT_ROOT=/mlflow/artifacts
    volumes:
      - mlflow-artifacts:/mlflow/artifacts
    ports:
      - "5000:5000"
    depends_on:
      - postgres
    networks:
      - nyxai-network
    restart: unless-stopped
    command: mlflow server --host 0.0.0.0 --port 5000

  # PTAL-GAT 模型服务（新增）
  ptal-gat-service:
    build:
      context: ./ptal-gat
      dockerfile: Dockerfile
    environment:
      - INFLUXDB_URL=http://influxdb:8086
      - NEO4J_URL=bolt://neo4j:7687
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - MODEL_PATH=/models/ptal_gat
    volumes:
      - ./ptal-gat/models:/models
      - ptal-gat-cache:/root/.cache
    ports:
      - "5001:5001"
    depends_on:
      - influxdb
      - neo4j
      - mlflow
    networks:
      - nyxai-network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]  # 可选：GPU 加速

  # 可视化服务
  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=neo4j-datasource
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"
    depends_on:
      - influxdb
      - neo4j
      - elasticsearch
    networks:
      - nyxai-network
    restart: unless-stopped

  # 数据采集层（模拟，实际部署在网关虚拟机）
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - nyxai-network
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.26.0
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"
    networks:
      - nyxai-network
    restart: unless-stopped

  # 监控与日志
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - nyxai-network
    restart: unless-stopped

networks:
  nyxai-network:
    driver: bridge

volumes:
  postgres-data:
  influxdb-data:
  neo4j-data:
  neo4j-logs:
  elasticsearch-data:
  chroma-data:
  mlflow-artifacts:
  grafana-data:
  prometheus-data:
  ptal-gat-cache:
```

### 6.2 部署架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose 部署架构                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    外部访问层                                    │
│  ├─ http://localhost:3000  → 前端界面                           │
│  ├─ http://localhost:8000  → 后端 API                          │
│  ├─ http://localhost:3001  → Grafana 大屏                      │
│  ├─ http://localhost:5000  → MLflow 模型管理                   │
│  └─ http://localhost:9090  → Prometheus                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    应用层 (Docker Containers)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ frontend     │  │ backend      │  │ ptal-gat-service     │  │
│  │ (React)      │  │ (FastAPI)    │  │ (PTAL-GAT 模型)      │  │
│  │ Port: 3000   │  │ Port: 8000   │  │ Port: 5001           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    数据存储层 (Docker Volumes)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ postgres     │  │ influxdb     │  │ neo4j                │  │
│  │ Port: 5432   │  │ Port: 8086   │  │ Port: 7474, 7687     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ elasticsearch│  │ chroma       │  │ mlflow               │  │
│  │ Port: 9200   │  │ Port: 8001   │  │ Port: 5000           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    监控与可视化层 (Docker Containers)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ grafana      │  │ prometheus   │  │ alertmanager         │  │
│  │ Port: 3001   │  │ Port: 9090   │  │ Port: 9093           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐                                               │
│  │ cadvisor     │  (容器监控)                                   │
│  │ Port: 8080   │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    数据采集层（外部部署）                         │
│  ├─ node-exporter (部署在网关虚拟机)                            │
│  ├─ nginx-lua-prometheus (部署在网关虚拟机)                     │
│  └─ filebeat (部署在网关虚拟机)                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 7. 项目目录结构设计

```
NyxAI/
├── backend/                              # Python 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI 入口
│   │   ├── config.py                     # 配置管理
│   │   │
│   │   ├── agents/                       # Agent 模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Agent 基类
│   │   │   ├── orchestrator.py           # 编排 Agent
│   │   │   ├── prediction.py             # 预测 Agent（新增）
│   │   │   ├── investigation.py          # 调查 Agent
│   │   │   ├── diagnosis.py              # 根因定界 Agent
│   │   │   └── recovery.py               # 恢复 Agent
│   │   │
│   │   ├── tools/                        # 工具模块
│   │   │   ├── __init__.py
│   │   │   ├── prometheus.py             # Prometheus 工具
│   │   │   ├── influxdb.py               # InfluxDB 工具
│   │   │   ├── loki.py                   # Loki 日志工具
│   │   │   ├── jaeger.py                 # Jaeger 链路工具
│   │   │   ├── knowledge.py              # 知识检索工具
│   │   │   ├── topology.py               # 拓扑工具（新增）
│   │   │   └── cmdb.py                   # CMDB 工具（新增）
│   │   │
│   │   ├── models/                       # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── session.py                # 会话模型
│   │   │   ├── evidence.py               # 证据模型
│   │   │   ├── knowledge.py              # 知识模型
│   │   │   ├── prediction.py             # 预测模型（新增）
│   │   │   ├── topology.py               # 拓扑模型（新增）
│   │   │   ├── alert.py                  # 告警模型（新增）
│   │   │   └── api.py                    # API 请求/响应模型
│   │   │
│   │   ├── api/                          # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py               # 会话 API
│   │   │   ├── chat.py                   # 对话 API
│   │   │   ├── knowledge.py              # 知识管理 API
│   │   │   ├── webhook.py                # Webhook 入口
│   │   │   ├── prediction.py             # 预测 API（新增）
│   │   │   ├── topology.py               # 拓扑 API（新增）
│   │   │   ├── alerts.py                 # 告警 API（新增）
│   │   │   └── model.py                  # 模型管理 API（新增）
│   │   │
│   │   ├── services/                     # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── llm.py                    # LLM 服务（多模型）
│   │   │   ├── vector_store.py           # 向量存储服务
│   │   │   ├── scheduler.py              # 定时任务服务
│   │   │   ├── topology_service.py       # 拓扑管理服务（新增）
│   │   │   ├── data_preprocess_service.py # 数据预处理服务（新增）
│   │   │   ├── model_training_service.py  # 模型训练服务（新增）
│   │   │   ├── model_inference_service.py # 模型推理服务（新增）
│   │   │   ├── anomaly_analysis_service.py # 异常分析服务（新增）
│   │   │   ├── alert_service.py          # 告警服务（新增）
│   │   │   └── notification_service.py   # 通知服务（新增）
│   │   │
│   │   ├── storage/                      # 存储层
│   │   │   ├── __init__.py
│   │   │   ├── database.py               # 数据库连接
│   │   │   └── repositories/             # 数据仓库
│   │   │       ├── __init__.py
│   │   │       ├── session_repo.py
│   │   │       ├── evidence_repo.py
│   │   │       ├── knowledge_repo.py
│   │   │       ├── prediction_repo.py    # 预测仓库（新增）
│   │   │       ├── topology_repo.py      # 拓扑仓库（新增）
│   │   │       └── alert_repo.py         # 告警仓库（新增）
│   │   │
│   │   └── utils/                        # 工具函数
│   │       ├── __init__.py
│   │       └── logger.py
│   │
│   ├── tests/                            # 测试
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   │   ├── test_prediction.py        # 预测 Agent 测试（新增）
│   │   │   └── ...
│   │   ├── test_tools/
│   │   │   ├── test_topology.py          # 拓扑工具测试（新增）
│   │   │   └── ...
│   │   ├── test_services/
│   │   │   ├── test_topology_service.py  # 拓扑服务测试（新增）
│   │   │   └── ...
│   │   └── test_api/
│   │       ├── test_prediction.py        # 预测 API 测试（新增）
│   │       └── ...
│   │
│   ├── skills/                           # Agent Skills
│   │   ├── brainstorming/
│   │   └── systematic-debugging/
│   │
│   ├── pyproject.toml                    # 项目配置
│   ├── uv.lock                           # uv 依赖锁定
│   ├── Dockerfile.backend                # 后端 Dockerfile
│   └── .env.example
│
├── frontend/                             # React 前端
│   ├── src/
│   │   ├── components/                   # 组件
│   │   │   ├── Chat/                     # 对话组件
│   │   │   ├── EvidenceChain/            # 证据链组件
│   │   │   ├── Knowledge/                # 知识管理组件
│   │   │   ├── Topology/                 # 拓扑组件（新增）
│   │   │   │   ├── TopologyGraph.tsx     # 拓扑图
│   │   │   │   ├── NodeDetail.tsx        # 节点详情
│   │   │   │   └── TopologyControls.tsx  # 拓扑控制
│   │   │   ├── Prediction/               # 预测组件（新增）
│   │   │   │   ├── PredictionPanel.tsx   # 预测面板
│   │   │   │   ├── AnomalyScore.tsx      # 异常分数
│   │   │   │   └── CascadeRisk.tsx       # 级联风险
│   │   │   ├── Alert/                    # 告警组件（新增）
│   │   │   │   ├── AlertList.tsx         # 告警列表
│   │   │   │   ├── AlertDetail.tsx       # 告警详情
│   │   │   │   └── AlertStatistics.tsx   # 告警统计
│   │   │   └── Model/                    # 模型组件（新增）
│   │   │       ├── ModelPerformance.tsx  # 模型性能
│   │   │       └── TrainingStatus.tsx    # 训练状态
│   │   │
│   │   ├── services/                     # API 服务
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   ├── predictionApi.ts          # 预测 API（新增）
│   │   │   ├── topologyApi.ts            # 拓扑 API（新增）
│   │   │   └── alertApi.ts               # 告警 API（新增）
│   │   │
│   │   ├── stores/                       # 状态管理
│   │   │   ├── sessionStore.ts
│   │   │   ├── predictionStore.ts        # 预测状态（新增）
│   │   │   ├── topologyStore.ts          # 拓扑状态（新增）
│   │   │   └── alertStore.ts             # 告警状态（新增）
│   │   │
│   │   ├── types/                        # 类型定义
│   │   │   ├── index.ts
│   │   │   ├── prediction.ts             # 预测类型（新增）
│   │   │   ├── topology.ts               # 拓扑类型（新增）
│   │   │   └── alert.ts                  # 告警类型（新增）
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile.frontend               # 前端 Dockerfile
│   └── .env.example
│
├── ptal-gat/                             # PTAL-GAT 模型服务（新增）
│   ├── models/                           # 模型文件
│   │   ├── ptal_gat.py                   # PTAL-GAT 模型定义
│   │   ├── trainer.py                    # 训练器
│   │   └── inference.py                  # 推理器
│   │
│   ├── services/                         # 服务层
│   │   ├── topology_service.py           # 拓扑服务
│   │   ├── data_preprocess_service.py    # 数据预处理服务
│   │   ├── training_service.py           # 训练服务
│   │   └── inference_service.py          # 推理服务
│   │
│   ├── api/                              # API 层
│   │   ├── __init__.py
│   │   └── main.py                       # FastAPI 入口
│   │
│   ├── utils/                            # 工具函数
│   │   ├── __init__.py
│   │   ├── metrics.py                    # 指标计算
│   │   └── visualization.py              # 可视化
│   │
│   ├── tests/                            # 测试
│   │   ├── test_model.py
│   │   ├── test_training.py
│   │   └── test_inference.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile                        # PTAL-GAT Dockerfile
│   └── README.md
│
├── grafana/                              # Grafana 配置（新增）
│   ├── dashboards/                       # 仪表板
│   │   ├── topology-dashboard.json       # 拓扑监控大屏
│   │   ├── prediction-dashboard.json     # 预测监控大屏
│   │   ├── alert-dashboard.json          # 告警监控大屏
│   │   └── model-performance-dashboard.json  # 模型性能大屏
│   │
│   └── datasources/                      # 数据源配置
│       ├── influxdb.yml
│       ├── neo4j.yml
│       └── elasticsearch.yml
│
├── prometheus/                           # Prometheus 配置（新增）
│   ├── prometheus.yml                    # Prometheus 配置
│   └── alerts.yml                        # 告警规则
│
├── alertmanager/                         # Alertmanager 配置（新增）
│   └── alertmanager.yml                  # Alertmanager 配置
│
├── docs/                                 # 文档
│   ├── superpowers/
│   │   ├── specs/                        # 设计规范
│   │   │   └── 2026-04-08-ptal-gat-integration-design.md  # 本设计文档
│   │   └── plans/                        # 实现计划
│   │       └── 2026-04-08-ptal-gat-integration-plan.md     # 实现计划
│   └── ptal.md                           # PRD 文档
│
├── docker-compose.yml                    # Docker Compose 配置
├── Dockerfile.backend                    # 后端 Dockerfile（根目录）
├── Dockerfile.frontend                   # 前端 Dockerfile（根目录）
├── .gitignore
└── README.md
```

## 8. 实施计划

### 8.1 总体规划

总周期：8周（56天），分5个阶段推进

### 8.2 第一阶段：基础设施搭建（第1-2周）

**核心任务：**

1. Docker 环境准备
   - 编写 docker-compose.yml
   - 配置 InfluxDB 1.x、Neo4j、Elasticsearch
   - 配置 PostgreSQL、Chroma、MLflow
   - 配置 Grafana、Prometheus、Alertmanager

2. 数据采集层部署
   - 部署 node-exporter（虚拟机性能指标）
   - 部署 nginx-lua-prometheus（网关业务指标）
   - 部署 filebeat（访问日志）
   - 配置数据上报路径

3. 数据存储测试
   - 测试 InfluxDB 时序数据存储与查询
   - 测试 Neo4j 拓扑数据存储与查询
   - 测试 Elasticsearch 日志存储与检索
   - 测试数据备份与恢复

4. 基础 API 框架搭建
   - 创建 prediction.py、topology.py、alerts.py、model.py API 路由
   - 创建对应的数据模型
   - 编写基础单元测试

**交付物：**
- 完整的 docker-compose.yml
- 数据采集层部署文档
- 数据存储测试报告
- 基础 API 框架代码

**验收标准：**
- 所有 Docker 容器正常运行
- 数据采集成功率 ≥ 99.9%
- 数据存储查询延迟符合要求
- 基础 API 测试通过率 100%

### 8.3 第二阶段：PTAL-GAT 模型服务开发（第3-4周）

**核心任务：**

1. PTAL-GAT 模型开发
   - 实现 PTAL-GAT 模型架构
   - 实现拓扑感知的图注意力机制
   - 实现物理先验锚定损失函数
   - 实现无监督训练流程

2. 数据预处理服务开发
   - 实现缺失值填充（前向填充 + 均值填充）
   - 实现特征归一化
   - 实现时序窗口划分
   - 实现异常数据过滤

3. 拓扑管理服务开发
   - 实现 CMDB 对接
   - 实现拓扑自动构建
   - 实现拓扑增量更新
   - 实现拓扑动态校验
   - 实现拓扑可视化

4. 模型训练服务开发
   - 实现全量预训练流程
   - 实现增量微调流程
   - 集成 MLflow 模型版本管理
   - 实现模型性能评估

5. 模型推理服务开发
   - 实现实时推理接口
   - 实现批量推理接口
   - 实现推理结果缓存
   - 优化推理延迟（< 100ms）

**交付物：**
- PTAL-GAT 模型代码
- 数据预处理服务代码
- 拓扑管理服务代码
- 模型训练/推理服务代码
- 模型性能测试报告

**验收标准：**
- 模型训练成功率 100%
- 推理延迟 < 100ms
- 异常检测 F1-Score ≥ 95%（基于测试数据）
- 拓扑构建准确率 ≥ 99.5%
- 数据预处理延迟 < 5s

### 8.4 第三阶段：Agent 集成与异常分析（第5-6周）

**核心任务：**

1. Prediction Agent 开发
   - 实现 Prediction Agent 类
   - 集成拓扑管理工具
   - 集成模型推理工具
   - 实现异常分析逻辑
   - 实现预测结果生成

2. Agent 协作流程开发
   - 更新 Orchestrator Agent（支持预测触发）
   - 实现 Prediction → Investigation 协作
   - 实现 Investigation → Diagnosis 协作（增强）
   - 实现 Diagnosis → Recovery 协作（增强）
   - 实现闭环优化流程

3. 告警服务开发
   - 实现告警生成逻辑
   - 实现告警收敛算法（基于拓扑）
   - 实现告警推送（短信、邮件、企业微信/钉钉）
   - 实现告警生命周期管理

4. 异常分析服务开发
   - 实现异常判定逻辑
   - 实现级联故障分析
   - 实现根因定位算法
   - 实现异常分析报告生成

**交付物：**
- Prediction Agent 代码
- Agent 协作流程代码
- 告警服务代码
- 异常分析服务代码
- 集成测试报告

**验收标准：**
- Prediction Agent 功能正常
- Agent 协作流程顺畅
- 告警响应时间 < 1 分钟
- 告警收敛率 ≥ 85%
- 根因定位 Top-3 准确率 ≥ 92%
- 级联故障预测准确率 ≥ 92%

### 8.5 第四阶段：前端界面与可视化（第7周）

**核心任务：**

1. 拓扑可视化组件开发
   - 实现拓扑图展示（D3.js / React Flow）
   - 实现节点状态标注
   - 实现边的依赖关系展示
   - 实现节点详情查看

2. 预测面板组件开发
   - 实现预测结果展示
   - 实现异常分数可视化
   - 实现级联风险展示
   - 实现根因候选展示

3. 告警管理组件开发
   - 实现告警列表展示
   - 实现告警详情查看
   - 实现告警确认/解决操作
   - 实现告警统计展示

4. 模型性能监控组件开发
   - 实现模型性能指标展示
   - 实现训练状态监控
   - 实现模型版本管理

5. Grafana 仪表板配置
   - 配置拓扑监控大屏
   - 配置预测监控大屏
   - 配置告警监控大屏
   - 配置模型性能大屏

**交付物：**
- 拓扑可视化组件代码
- 预测面板组件代码
- 告警管理组件代码
- 模型性能监控组件代码
- Grafana 仪表板配置文件
- 前端测试报告

**验收标准：**
- 所有前端组件功能正常
- 界面响应流畅（加载时间 < 2秒）
- 可视化清晰、实时更新（更新频率 ≤ 10s）
- Grafana 仪表板展示正常
- 前端测试覆盖率 ≥ 80%

### 8.6 第五阶段：集成测试与上线（第8周）

**核心任务：**

1. 端到端测试
   - 测试完整预测流程（采集 → 预测 → 告警）
   - 测试完整诊断流程（预测 → 调查 → 诊断 → 恢复）
   - 测试拓扑变更适配流程
   - 测试闭环优化流程

2. 性能测试
   - 测试推理延迟（目标 < 100ms）
   - 测试告警响应时间（目标 < 1分钟）
   - 测试系统并发能力（支持 100+ 网关节点）
   - 测试系统稳定性（连续运行 72 小时）

3. 压力测试
   - 模拟高并发场景（100 个节点同时上报数据）
   - 模拟拓扑大幅变更（≥ 20% 节点调整）
   - 模拟故障场景（组件异常、网络中断）
   - 测试系统恢复能力

4. 用户培训
   - 编写用户手册
   - 编写运维手册
   - 编写 API 文档
   - 开展培训会议

5. 正式上线
   - 部署到生产环境
   - 开启实时监控
   - 开启告警推送
   - 安排专人值守

**交付物：**
- 端到端测试报告
- 性能测试报告
- 压力测试报告
- 用户手册
- 运维手册
- API 文档
- 系统上线报告

**验收标准：**
- 所有端到端测试通过
- 性能指标达标
- 系统稳定性达标（连续运行 72 小时无崩溃）
- 文档完善、培训完成
- 系统正式上线运行

## 9. 验收标准

### 9.1 功能验收标准

**数据采集层：**
- 18 维核心指标采集完整
- 访问日志采集完整
- 采集成功率 ≥ 99.9%
- 数据上报成功率 ≥ 99.9%
- 采集延迟 < 1s

**核心平台层：**

拓扑管理：
- 拓扑构建准确率 ≥ 99.5%
- 常规变更适配时间 < 5 分钟
- 动态校验一致率 ≥ 99%

数据预处理：
- 预处理后无缺失值、无量纲差异
- 预处理延迟 < 5s

模型训练/推理：
- 全量训练时间 < 8 小时
- 增量微调时间 < 2 小时
- 推理延迟 < 100ms

异常分析：
- 异常检测 F1-Score ≥ 95%
- 根因定位 Top-3 准确率 ≥ 92%
- 级联故障预测准确率 ≥ 92%

告警/可视化：
- 告警响应时间 < 1 分钟
- 告警收敛率 ≥ 85%
- 可视化界面实时更新（更新频率 ≤ 10s）

数据存储：
- InfluxDB 查询延迟 < 500ms
- Elasticsearch 检索延迟 ≤ 1s
- 数据备份恢复功能正常

**Agent 协作层：**
- Prediction Agent 功能正常
- Agent 协作流程顺畅
- 预测 → 诊断 → 恢复闭环完整
- 闭环优化有效

**运维闭环层：**
- 处置指令下发延迟 < 10s
- 执行结果反馈及时
- 闭环优化后误报率 < 4%
- MTTR 缩短 60% 以上

### 9.2 非功能验收标准

**性能：**
- 核心平台推理延迟 < 100ms
- 系统可用性 ≥ 99.9%
- 网关侧 CPU 占用 < 5%
- 支持 100+ 网关节点并发处理

**兼容性：**
- 适配主流 Linux 系统（Ubuntu 22.04、CentOS 8）
- 适配主流浏览器（Chrome、Firefox、Edge，版本 ≥ 80）
- 组件间兼容无冲突
- Docker 部署正常

**安全性：**
- 数据加密传输
- 权限隔离（RBAC）
- 日志不可篡改
- 具备异常防护能力

**可靠性：**
- 系统连续运行 72 小时无崩溃
- 组件异常可自动自愈
- 数据无丢失
- 备份恢复功能正常

**可维护性：**
- 支持 Docker 一键部署
- 故障排查时间 ≤ 30 分钟
- 文档完善
- 支持动态扩容

### 9.3 验收流程

**分阶段验收：**
- 每个阶段结束后，由产品、开发、测试、运维人员共同验收
- 出具阶段验收报告
- 问题整改后重新验收

**全量验收：**
- 系统上线后，运行 7 天
- 测试全流程功能、性能
- 确认满足所有需求后，出具最终验收报告
- 问题整改后重新验收

**验收标准：**
- 所有功能验收标准达标
- 所有非功能验收标准达标
- 所有测试通过
- 文档完善、培训完成

## 10. 风险与规避方案

| 风险类型 | 具体风险描述 | 影响程度 | 规避方案 |
|---------|------------|---------|---------|
| 数据风险 | 采集组件异常、网络中断，导致数据丢失、缺失，影响模型推理精度 | 中 | 1. 采集组件支持自动重启，异常时上报告警；2. 网络中断时本地缓存数据（≤1小时），恢复后自动续传；3. 预处理阶段采用多种填充方式，降低缺失值影响 |
| 拓扑风险 | CMDB信息错误、配置解析失败，导致拓扑构建错误，模型性能骤降 | 高 | 1. 采用静态先验+动态流量校验双机制，每日校验拓扑准确性；2. 拓扑变更后，先离线验证，再同步至推理模块；3. 设置拓扑错误告警，偏差超过20%时暂停更新，人工校验 |
| 模型风险 | 拓扑大幅变更后，模型性能波动过大；无监督训练导致误报率、漏报率过高 | 中 | 1. 拓扑大幅变更后自动触发增量微调，确保性能稳定；2. 每月优化异常阈值，结合故障处置记录调整模型参数；3. 保留纯时序分支作为兜底，避免漏检 |
| 部署风险 | Docker 环境配置错误、组件兼容性冲突，导致部署失败或系统不稳定 | 中 | 1. 部署前检查环境配置，确保满足资源要求；2. 选择兼容的开源组件版本，提前做兼容性测试；3. 支持一键回滚，部署失败时快速恢复至初始状态 |
| 运维风险 | 运维人员不熟悉系统操作，导致故障处置不及时；告警风暴增加运维工作量 | 低 | 1. 开展全面用户培训，提供详细运维手册；2. 实现告警收敛，避免关联告警重复推送；3. 配置告警分级，按职责分配告警，提升处置效率 |

## 11. 总结

本设计文档详细描述了将 PTAL-GAT 故障预测系统深度集成到现有 NyxAI 系统的完整方案。通过统一架构、Agent 协作、数据统一、Docker 部署等核心设计理念，实现了"预测 → 诊断 → 恢复"的完整闭环。

**核心价值：**
1. 从反应式运维转向预测式运维
2. 提前 15-60 分钟预警潜在故障
3. 异常检测精度提升（F1-Score ≥ 95%）
4. 根因定位准确率提升（Top-3 ≥ 92%）
5. 告警收敛率 ≥ 85%，减少告警风暴
6. MTTR 缩短 60% 以上

**实施保障：**
1. 分阶段实施，降低风险
2. 明确的交付物和验收标准
3. 完善的风险规避方案
4. Docker 统一部署，简化运维

通过本方案的实施，NyxAI 将成为具备预测能力的智能运维平台，为 OpenResty 三级全球分布式 API 网关提供全方位的故障预测、诊断和恢复能力。
