# NyxAI - 多Agent协作运维智能体系统

NyxAI 是一个基于多Agent协作的运维智能体系统，支持自主调查观测数据、根因定界、故障恢复，并生成证据链报告。

## ✨ 核心特性

- **多Agent协作**: Orchestrator + Investigation + Diagnosis + Recovery 四层Agent架构
- **证据链模型**: 支持 supports/contradicts 关系的因果推理
- **知识注入**: 每个Agent可加载特定领域知识
- **多数据源**: 支持 Prometheus、InfluxDB、Loki、Jaeger
- **半自动恢复**: 风险评估 + 人工确认机制
- **现代化界面**: React + Ant Design 对话式交互

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React + Ant Design)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ ChatWindow  │  │EvidenceChain│  │  CausalGraph        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + PydanticAI)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Layer                          │   │
│  │  /api/v1/chat  /api/v1/sessions  /webhook/alert      │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Agent Orchestration                   │   │
│  │  ┌────────────┐ ┌───────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │Orchestrator│→│Investigate│→│Diagnose│→│Recovery│  │   │
│  │  └────────────┘ └───────────┘ └────────┘ └────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Tools & Data Layer                       │   │
│  │  ┌──────────┐ ┌────────┐ ┌──────┐ ┌────────┐        │   │
│  │  │Prometheus│ │InfluxDB│ │ Loki │ │ Jaeger │        │   │
│  │  └──────────┘ └────────┘ └──────┘ └────────┘        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- uv (Python包管理器)

### 后端启动

```bash
cd backend

# 安装依赖
uv sync

# 复制配置文件
cp .env.example .env

# 启动服务
uv run uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

## 📁 项目结构

```
NyxAI/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent实现
│   │   │   ├── base.py      # Agent基类
│   │   │   ├── orchestrator.py
│   │   │   ├── investigation.py
│   │   │   ├── diagnosis.py
│   │   │   └── recovery.py
│   │   ├── api/             # API路由
│   │   │   ├── chat.py
│   │   │   ├── sessions.py
│   │   │   ├── knowledge.py
│   │   │   └── webhook.py
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 服务层
│   │   ├── storage/         # 存储层
│   │   ├── tools/           # 观测工具
│   │   └── config.py
│   ├── tests/               # 测试用例
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   └── Evidence/
│   │   ├── services/
│   │   └── stores/
│   └── package.json
├── docs/
│   └── superpowers/
│       ├── specs/           # 设计规范
│       └── plans/           # 实现计划
└── docker-compose.yml
```

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接 | sqlite+aiosqlite:///./nyxai.db |
| `LLM_PROVIDER` | LLM提供商 | openai |
| `LLM_MODEL` | 模型名称 | gpt-4o |
| `LLM_API_KEY` | API密钥 | - |
| `PROMETHEUS_URL` | Prometheus地址 | - |
| `INFLUXDB_URL` | InfluxDB地址 | - |
| `LOKI_URL` | Loki地址 | - |
| `JAEGER_URL` | Jaeger地址 | - |

## 📡 API 端点

### Chat API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/message` | 发送消息 |
| POST | `/api/v1/chat/stream` | 流式响应 (SSE) |
| GET | `/api/v1/chat/{session_id}/evidence` | 获取证据链 |

### Session API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/sessions` | 列出会话 |
| GET | `/api/v1/sessions/{id}` | 获取会话详情 |

### Webhook API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/webhook/alert` | Prometheus告警 |
| POST | `/webhook/custom` | 自定义事件 |

## 🧪 测试

```bash
cd backend
uv run pytest tests/ -v
```

## 📄 License

MIT
