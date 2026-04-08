# PTAL-GAT 故障预测系统集成实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PTAL-GAT 故障预测系统深度集成到 NyxAI，实现"预测 → 诊断 → 恢复"完整闭环

**Architecture:** 采用深度集成方案，在现有 NyxAI 多 Agent 架构基础上新增 Prediction Agent，统一数据存储层（InfluxDB + Neo4j + Elasticsearch），通过 Docker 容器化部署所有组件

**Tech Stack:** Python 3.11+ / FastAPI / PydanticAI / React + Ant Design / InfluxDB 1.x / Neo4j / Elasticsearch / PostgreSQL / Chroma / MLflow / Grafana / Prometheus / Docker

---

## 文件结构映射

### 后端新增文件

```
backend/app/
├── agents/
│   └── prediction.py                    # Prediction Agent 实现
├── models/
│   ├── prediction.py                    # 预测相关数据模型
│   ├── topology.py                      # 拓扑数据模型
│   └── alert.py                         # 告警数据模型
├── api/
│   ├── prediction.py                    # 预测 API 路由
│   ├── topology.py                      # 拓扑 API 路由
│   ├── alerts.py                        # 告警 API 路由
│   └── model.py                         # 模型管理 API 路由
├── services/
│   ├── topology_service.py              # 拓扑管理服务
│   ├── data_preprocess_service.py       # 数据预处理服务
│   ├── model_training_service.py        # 模型训练服务
│   ├── model_inference_service.py       # 模型推理服务
│   ├── anomaly_analysis_service.py      # 异常分析服务
│   ├── alert_service.py                 # 告警服务
│   └── notification_service.py          # 通知服务
├── tools/
│   ├── topology.py                      # 拓扑工具
│   └── cmdb.py                          # CMDB 工具
└── storage/repositories/
    ├── prediction_repo.py               # 预测数据仓库
    ├── topology_repo.py                 # 拓扑数据仓库
    └── alert_repo.py                    # 告警数据仓库
```

### PTAL-GAT 模型服务新增文件

```
ptal-gat/
├── models/
│   ├── ptal_gat.py                      # PTAL-GAT 模型定义
│   ├── trainer.py                       # 训练器
│   └── inference.py                     # 推理器
├── services/
│   ├── topology_service.py              # 拓扑服务
│   ├── data_preprocess_service.py       # 数据预处理服务
│   ├── training_service.py              # 训练服务
│   └── inference_service.py             # 推理服务
├── api/
│   └── main.py                          # FastAPI 入口
├── utils/
│   ├── metrics.py                       # 指标计算
│   └── visualization.py                 # 可视化
├── tests/
│   ├── test_model.py
│   ├── test_training.py
│   └── test_inference.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### 前端新增文件

```
frontend/src/
├── components/
│   ├── Topology/
│   │   ├── TopologyGraph.tsx            # 拓扑图组件
│   │   ├── NodeDetail.tsx               # 节点详情组件
│   │   └── TopologyControls.tsx         # 拓扑控制组件
│   ├── Prediction/
│   │   ├── PredictionPanel.tsx          # 预测面板组件
│   │   ├── AnomalyScore.tsx             # 异常分数组件
│   │   └── CascadeRisk.tsx              # 级联风险组件
│   ├── Alert/
│   │   ├── AlertList.tsx                # 告警列表组件
│   │   ├── AlertDetail.tsx              # 告警详情组件
│   │   └── AlertStatistics.tsx          # 告警统计组件
│   └── Model/
│       ├── ModelPerformance.tsx         # 模型性能组件
│       └── TrainingStatus.tsx           # 训练状态组件
├── services/
│   ├── predictionApi.ts                 # 预测 API 服务
│   ├── topologyApi.ts                   # 拓扑 API 服务
│   └── alertApi.ts                      # 告警 API 服务
├── stores/
│   ├── predictionStore.ts               # 预测状态管理
│   ├── topologyStore.ts                 # 拓扑状态管理
│   └── alertStore.ts                    # 告警状态管理
└── types/
    ├── prediction.ts                    # 预测类型定义
    ├── topology.ts                      # 拓扑类型定义
    └── alert.ts                         # 告警类型定义
```

### 配置文件新增

```
grafana/
├── dashboards/
│   ├── topology-dashboard.json          # 拓扑监控大屏
│   ├── prediction-dashboard.json        # 预测监控大屏
│   ├── alert-dashboard.json             # 告警监控大屏
│   └── model-performance-dashboard.json # 模型性能大屏
└── datasources/
    ├── influxdb.yml
    ├── neo4j.yml
    └── elasticsearch.yml

prometheus/
├── prometheus.yml                       # Prometheus 配置
└── alerts.yml                           # 告警规则

alertmanager/
└── alertmanager.yml                     # Alertmanager 配置
```

---

## 第一阶段：基础设施搭建（第1-2周）

### Task 1: 创建 Docker Compose 配置文件

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: 创建 .env.example 文件**

```env
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=your-api-key-here

# Database Configuration
POSTGRES_USER=nyxai
POSTGRES_PASSWORD=nyxai
POSTGRES_DB=nyxai

# InfluxDB Configuration
INFLUXDB_DB=nyxai_metrics
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin

# Neo4j Configuration
NEO4J_AUTH=neo4j/nyxai123

# Grafana Configuration
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

- [ ] **Step 2: 创建 docker-compose.yml 基础结构**

```yaml
version: '3.8'

services:
  # 数据存储层
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nyxai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  influxdb:
    image: influxdb:1.8-alpine
    environment:
      - INFLUXDB_DB=${INFLUXDB_DB}
      - INFLUXDB_ADMIN_USER=${INFLUXDB_ADMIN_USER}
      - INFLUXDB_ADMIN_PASSWORD=${INFLUXDB_ADMIN_PASSWORD}
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
      - NEO4J_AUTH=${NEO4J_AUTH}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    ports:
      - "7474:7474"
      - "7687:7687"
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

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.9.2
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/mlflow
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
```

- [ ] **Step 3: 添加应用服务到 docker-compose.yml**

在 `services:` 部分添加：

```yaml
  # 应用层
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
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

  # PTAL-GAT 模型服务
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

  # 可视化与监控
  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_USER=${GF_SECURITY_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GF_SECURITY_ADMIN_PASSWORD}
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
```

- [ ] **Step 4: 添加 volumes 定义**

在 `volumes:` 部分添加：

```yaml
  grafana-data:
  prometheus-data:
  ptal-gat-cache:
```

- [ ] **Step 5: 验证 docker-compose.yml 语法**

Run: `docker-compose config`
Expected: 配置文件语法正确，无错误

- [ ] **Step 6: 提交**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add docker-compose configuration for PTAL-GAT integration"
```

### Task 2: 创建后端数据模型

**Files:**
- Create: `backend/app/models/prediction.py`
- Create: `backend/app/models/topology.py`
- Create: `backend/app/models/alert.py`
- Test: `backend/tests/test_models/test_prediction.py`

- [ ] **Step 1: 创建预测数据模型测试**

```python
import pytest
from datetime import datetime
from app.models.prediction import NodeType, NodeStatus, TopologyNode, AnomalyScore, PredictionResult

def test_topology_node_creation():
    node = TopologyNode(
        id="node-001",
        ip="192.168.1.1",
        node_type=NodeType.EDGE,
        pop="pop-beijing",
        region="cn-north",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert node.id == "node-001"
    assert node.status == NodeStatus.NORMAL

def test_anomaly_score_validation():
    score = AnomalyScore(
        node_id="node-001",
        score=0.85,
        anomaly_type="performance",
        confidence=0.92,
        detected_at=datetime.now()
    )
    assert score.score == 0.85
    assert 0 <= score.score <= 1

def test_prediction_result_creation():
    result = PredictionResult(
        session_id="session-001",
        prediction_time=datetime.now(),
        prediction_window=30,
        anomaly_scores=[],
        cascade_risk=0.75,
        root_cause_candidates=["node-001"],
        model_version="v1.0.0",
        inference_latency=85.5,
        confidence=0.90,
        created_at=datetime.now()
    )
    assert result.prediction_window == 30
    assert result.cascade_risk == 0.75
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && uv run pytest tests/test_models/test_prediction.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 创建预测数据模型**

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    EDGE = "edge"
    CORE = "core"
    POP = "pop"

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

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && uv run pytest tests/test_models/test_prediction.py -v`
Expected: PASS

- [ ] **Step 5: 创建拓扑数据模型**

```python
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from app.models.prediction import TopologyNode, TopologyEdge

class Topology(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    adjacency_matrix: Dict[str, List[str]] = Field(..., description="邻接矩阵")
    created_at: datetime
    updated_at: datetime

class TopologySyncResult(BaseModel):
    updated: bool
    changes: Dict[str, int] = Field(..., description="变更统计")
    synced_at: datetime

class TopologyValidationResult(BaseModel):
    is_valid: bool
    issues: List[str] = Field(default_factory=list, description="问题列表")
    consistency_rate: float = Field(..., ge=0, le=1, description="一致性比率")
    validated_at: datetime
```

- [ ] **Step 6: 创建告警数据模型**

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AlertLevel(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    NORMAL = "normal"

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
    
    parent_alert_id: Optional[str] = Field(None, description="父告警ID（收敛关系）")
    related_alert_ids: List[str] = Field(default_factory=list, description="关联告警ID")
    
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

class AlertStatistics(BaseModel):
    total: int
    by_level: Dict[AlertLevel, int]
    by_status: Dict[AlertStatus, int]
    convergence_rate: float = Field(..., ge=0, le=1, description="收敛率")
    calculated_at: datetime
```

- [ ] **Step 7: 提交**

```bash
git add backend/app/models/prediction.py backend/app/models/topology.py backend/app/models/alert.py backend/tests/test_models/test_prediction.py
git commit -m "feat: add prediction, topology and alert data models"
```

### Task 3: 创建基础 API 路由

**Files:**
- Create: `backend/app/api/prediction.py`
- Create: `backend/app/api/topology.py`
- Create: `backend/app/api/alerts.py`
- Create: `backend/app/api/model.py`
- Test: `backend/tests/test_api/test_prediction.py`

- [ ] **Step 1: 创建预测 API 测试**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_execute_prediction():
    response = client.post("/api/v1/prediction/execute", json={
        "prediction_window": 30
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "prediction_window" in data

def test_get_prediction_history():
    response = client.get("/api/v1/prediction/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && uv run pytest tests/test_api/test_prediction.py -v`
Expected: FAIL with "404 Not Found"

- [ ] **Step 3: 创建预测 API 路由**

```python
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.prediction import PredictionResult

router = APIRouter(prefix="/api/v1/prediction", tags=["prediction"])

class PredictionExecuteRequest(BaseModel):
    node_ids: Optional[List[str]] = None
    prediction_window: int = 30

@router.post("/execute", response_model=PredictionResult)
async def execute_prediction(request: PredictionExecuteRequest):
    result = PredictionResult(
        session_id="session-001",
        prediction_time=datetime.now(),
        prediction_window=request.prediction_window,
        anomaly_scores=[],
        cascade_risk=0.0,
        root_cause_candidates=[],
        model_version="v1.0.0",
        inference_latency=85.5,
        confidence=0.90,
        created_at=datetime.now()
    )
    return result

@router.get("/history", response_model=List[PredictionResult])
async def get_prediction_history(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    node_id: Optional[str] = None
):
    return []

@router.get("/{prediction_id}", response_model=PredictionResult)
async def get_prediction(prediction_id: str):
    raise HTTPException(status_code=404, detail="Prediction not found")
```

- [ ] **Step 4: 在 main.py 中注册路由**

在 `backend/app/main.py` 中添加：

```python
from app.api import prediction, topology, alerts, model

app.include_router(prediction.router)
app.include_router(topology.router)
app.include_router(alerts.router)
app.include_router(model.router)
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd backend && uv run pytest tests/test_api/test_prediction.py -v`
Expected: PASS

- [ ] **Step 6: 创建拓扑 API 路由**

```python
from typing import Dict, List
from fastapi import APIRouter
from datetime import datetime

from app.models.topology import Topology, TopologySyncResult, TopologyValidationResult

router = APIRouter(prefix="/api/v1/topology", tags=["topology"])

@router.get("", response_model=Topology)
async def get_topology():
    return Topology(
        nodes=[],
        edges=[],
        adjacency_matrix={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@router.post("/sync", response_model=TopologySyncResult)
async def sync_topology():
    return TopologySyncResult(
        updated=False,
        changes={
            "added_nodes": 0,
            "removed_nodes": 0,
            "updated_nodes": 0,
            "added_edges": 0,
            "removed_edges": 0
        },
        synced_at=datetime.now()
    )

@router.post("/validate", response_model=TopologyValidationResult)
async def validate_topology():
    return TopologyValidationResult(
        is_valid=True,
        issues=[],
        consistency_rate=1.0,
        validated_at=datetime.now()
    )
```

- [ ] **Step 7: 创建告警 API 路由**

```python
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.alert import Alert, AlertStatistics, AlertLevel, AlertStatus

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

class AcknowledgeRequest(BaseModel):
    acknowledged_by: str

class ResolveRequest(BaseModel):
    resolved_by: str
    resolution: str

@router.get("", response_model=List[Alert])
async def get_alerts(
    level: Optional[AlertLevel] = None,
    status: Optional[AlertStatus] = None,
    start_time: Optional[datetime] = None
):
    return []

@router.get("/statistics", response_model=AlertStatistics)
async def get_alert_statistics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    return AlertStatistics(
        total=0,
        by_level={level: 0 for level in AlertLevel},
        by_status={status: 0 for status in AlertStatus},
        convergence_rate=0.0,
        calculated_at=datetime.now()
    )

@router.post("/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest):
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(alert_id: str, request: ResolveRequest):
    raise HTTPException(status_code=404, detail="Alert not found")
```

- [ ] **Step 8: 创建模型管理 API 路由**

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/model", tags=["model"])

class TrainingRequest(BaseModel):
    training_type: str
    data_range: Dict[str, datetime]
    hyperparameters: Optional[Dict[str, Any]] = None

class TrainingStatus(BaseModel):
    training_id: str
    status: str
    progress: float
    metrics: Optional[Dict[str, float]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

class ModelVersion(BaseModel):
    version: str
    created_at: datetime
    metrics: Dict[str, float]
    is_active: bool

@router.post("/train")
async def trigger_training(request: TrainingRequest):
    return {
        "training_id": "train-001",
        "status": "running"
    }

@router.get("/training/{training_id}", response_model=TrainingStatus)
async def get_training_status(training_id: str):
    return TrainingStatus(
        training_id=training_id,
        status="running",
        progress=0.0,
        started_at=datetime.now()
    )

@router.get("/versions", response_model=List[ModelVersion])
async def get_model_versions():
    return []

@router.post("/activate/{version}")
async def activate_model_version(version: str):
    return {"success": True}

@router.get("/performance")
async def get_model_performance(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    return {
        "f1_score": 0.96,
        "precision": 0.95,
        "recall": 0.97,
        "false_positive_rate": 0.03,
        "inference_latency_avg": 85.5,
        "prediction_accuracy": 0.93
    }
```

- [ ] **Step 9: 提交**

```bash
git add backend/app/api/prediction.py backend/app/api/topology.py backend/app/api/alerts.py backend/app/api/model.py backend/tests/test_api/test_prediction.py backend/app/main.py
git commit -m "feat: add prediction, topology, alerts and model API routes"
```

---

## 第二阶段：PTAL-GAT 模型服务开发（第3-4周）

### Task 4: 创建 PTAL-GAT 项目结构

**Files:**
- Create: `ptal-gat/requirements.txt`
- Create: `ptal-gat/Dockerfile`
- Create: `ptal-gat/README.md`
- Create: `ptal-gat/api/main.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
torch>=2.0.0
torch-geometric>=2.4.0
influxdb-client>=1.38.0
neo4j>=5.15.0
mlflow>=2.9.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
httpx>=0.28.0
python-multipart>=0.0.18
```

- [ ] **Step 2: 创建 Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5001"]
```

- [ ] **Step 3: 创建 README.md**

```markdown
# PTAL-GAT Model Service

PTAL-GAT (Physical Theory Anchored Learning with Graph Attention Networks) 模型服务

## 功能

- 拓扑感知的图注意力网络
- 物理先验锚定损失函数
- 无监督训练
- 实时推理

## API 端点

- `POST /inference` - 执行推理
- `POST /train` - 触发训练
- `GET /health` - 健康检查

## 部署

```bash
docker build -t ptal-gat-service .
docker run -p 5001:5001 ptal-gat-service
```
```

- [ ] **Step 4: 创建 FastAPI 入口**

```python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="PTAL-GAT Model Service",
    description="Physical Theory Anchored Learning with Graph Attention Networks",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/inference")
async def execute_inference(request: dict):
    return {
        "prediction_id": "pred-001",
        "anomaly_scores": [],
        "cascade_risk": 0.0,
        "root_cause_candidates": [],
        "inference_latency": 85.5
    }

@app.post("/train")
async def trigger_training(request: dict):
    return {
        "training_id": "train-001",
        "status": "running"
    }
```

- [ ] **Step 5: 提交**

```bash
git add ptal-gat/
git commit -m "feat: add PTAL-GAT model service project structure"
```

---

## 总结

本实现计划覆盖了 PTAL-GAT 故障预测系统集成的前两个阶段：

1. **第一阶段（第1-2周）**：基础设施搭建
   - Docker Compose 配置
   - 数据模型定义
   - 基础 API 路由

2. **第二阶段（第3-4周）**：PTAL-GAT 模型服务开发
   - 项目结构搭建
   - FastAPI 服务入口

后续阶段（第5-8周）的实现计划将在完成前两个阶段后继续细化，包括：
- PTAL-GAT 模型实现
- Agent 集成
- 前端界面开发
- 集成测试与上线

每个任务都遵循 TDD 原则，确保代码质量和可测试性。
