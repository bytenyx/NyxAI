# NyxAI

NyxAI 是一个智能运维系统（Agentic AIOps System），实现异常智能检测、智能根因定界与自动恢复功能。

## 核心功能

- **异常智能检测**: 支持统计方法、机器学习、深度学习等多种检测算法
- **智能根因定界**: 基于拓扑分析、维度归因和 LLM 辅助的根因分析
- **自动恢复系统**: 分级恢复策略，支持自动、半自动和人工介入模式
- **多 Agent 协作**: Monitor、Analyze、Decide、Execute、Learn 五类 Agent 协同工作

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        NyxAI AIOps Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  Data Collection → Anomaly Detection → RCA → Auto Recovery      │
│       ↓                  ↓              ↓           ↓          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Agent Orchestration Layer                   │   │
│  │  [Monitor] → [Analyze] → [Decide] → [Execute] → [Learn] │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Knowledge Base & LLM Layer                  │   │
│  │  [Incident KB]    [Runbook KB]    [LLM Service]         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术选型 |
|-----|---------|
| 后端框架 | FastAPI + Python 3.11+ |
| 指标观测 | Prometheus (采集、存储、查询) |
| 日志聚合 | Loki |
| 数据库 | PostgreSQL 15 + pgvector |
| 缓存/任务队列 | Redis 7 + Celery |
| 机器学习 | PyTorch + Scikit-learn |
| LLM | OpenAI / Claude / Ollama |
| 部署 | Docker + Kubernetes |

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- Make (可选)

### 本地开发（推荐 - 嵌入式数据库模式）

**方式一：使用启动脚本（最简单）**

1. 克隆仓库
```bash
git clone https://github.com/your-org/nyxai.git
cd nyxai
```

2. 安装依赖
```bash
pip install -e ".[dev]"
```

3. 配置环境变量
```bash
cp .env.local.example .env.local
# 编辑 .env.local 文件，设置你的 OPENAI_API_KEY
```

4. 启动服务
```bash
# Windows
python scripts/dev-start.py
# 或带自动重载
python scripts/dev-start.py --reload

# 或使用批处理脚本
scripts\dev-start.bat
scripts\dev-start.bat --reload

# 或使用 PowerShell
.\scripts\dev-start.ps1 -Reload
```

5. 访问服务
- API 文档: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**方式二：使用 Docker Compose（嵌入式模式）**

```bash
# 使用嵌入式数据库配置（无需 PostgreSQL/Redis）
cp .env.embedded.example .env
docker-compose -f docker-compose.embedded.yml up -d
```

**方式三：使用 Docker Compose（完整模式）**

```bash
# 使用完整配置（需要 PostgreSQL + Redis）
cp deployments/docker/.env.example .env
docker-compose up -d
```

### 开发特性

- **嵌入式数据库**: 使用 SQLite + ChromaDB，无需安装 PostgreSQL/Redis
- **自动重载**: 代码修改后自动重启服务
- **本地数据**: 所有数据存储在 `./data/` 目录，可随时删除重置
- **调试模式**: 默认启用 DEBUG，显示详细的错误信息

### API 端点

#### 健康检查
```bash
GET /health
GET /health/ready
GET /health/live
```

#### 异常管理
```bash
GET    /api/v1/anomalies          # 获取异常列表
GET    /api/v1/anomalies/{id}     # 获取异常详情
POST   /api/v1/anomalies          # 创建异常
PUT    /api/v1/anomalies/{id}     # 更新异常
POST   /api/v1/anomalies/{id}/acknowledge  # 确认异常
POST   /api/v1/anomalies/{id}/resolve      # 解决异常
```

#### 指标查询
```bash
GET /api/v1/metrics/query         # PromQL 即时查询
GET /api/v1/metrics/query_range   # PromQL 范围查询
GET /api/v1/metrics/labels        # 获取标签列表
GET /api/v1/metrics/label_values  # 获取标签值
```

## 项目结构

```
nyxai/
├── src/nyxai/
│   ├── api/                    # REST API 层
│   ├── agents/                 # Agent 编排层
│   ├── collectors/             # 数据采集层
│   ├── detection/              # 异常检测引擎
│   ├── rca/                    # 根因分析引擎
│   ├── recovery/               # 自动恢复引擎
│   ├── knowledge_base/         # 知识库
│   ├── llm/                    # LLM 服务
│   ├── storage/                # 数据存储
│   ├── config.py               # 配置管理
│   └── utils.py                # 工具函数
├── tests/                      # 测试
├── deployments/                # 部署配置
├── docs/                       # 文档
└── notebooks/                  # Jupyter Notebooks
```

## 开发指南

### 安装依赖

```bash
pip install -e ".[dev]"
```

### 代码检查

```bash
ruff check .
mypy src/nyxai
```

### 运行测试

```bash
pytest
```

### 数据库迁移

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 配置说明

核心配置通过环境变量管理，前缀为 `NYX_`：

| 变量名 | 说明 | 默认值 |
|-------|------|-------|
| NYX_DATABASE_URL | PostgreSQL 连接字符串 | postgresql+asyncpg://localhost/nyxai |
| NYX_REDIS_URL | Redis 连接字符串 | redis://localhost:6379 |
| NYX_PROMETHEUS_URL | Prometheus 地址 | http://localhost:9090 |
| NYX_LOKI_URL | Loki 地址 | http://localhost:3100 |
| NYX_OPENAI_API_KEY | OpenAI API 密钥 | - |
| NYX_ANTHROPIC_API_KEY | Claude API 密钥 | - |

## 许可证

[Apache License 2.0](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目主页: https://github.com/your-org/nyxai
- 文档: https://nyxai.readthedocs.io
