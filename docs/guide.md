# NyxAI 使用指南

> 智能 AIOps 平台 - 基于 AI 的异常检测、根因分析和自动恢复

---

## 目录

1. [快速开始](#快速开始)
2. [安装指南](#安装指南)
3. [配置说明](#配置说明)
4. [启动方式](#启动方式)
5. [API 使用](#api-使用)
6. [核心功能](#核心功能)
7. [故障排查](#故障排查)

---

## 快速开始

### 方式一：本地开发启动（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/nyxai.git
cd nyxai

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置环境变量
cp .env.local.example .env.local
# 编辑 .env.local，设置 OPENAI_API_KEY

# 4. 启动服务
python scripts/dev-start.py

# 5. 访问应用
# API 文档: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

### 方式二：Docker 启动（嵌入式模式）

```bash
# 使用嵌入式数据库（SQLite + ChromaDB）
cp .env.embedded.example .env
docker-compose -f docker-compose.embedded.yml up -d
```

---

## 安装指南

### 环境要求

- **Python**: 3.11 或更高版本
- **操作系统**: Windows, macOS, Linux
- **内存**: 最低 2GB，推荐 4GB
- **磁盘**: 最低 1GB 可用空间

### 安装步骤

#### 1. 安装 Python 依赖

```bash
# 基础安装
pip install -e .

# 开发安装（包含所有开发依赖）
pip install -e ".[dev]"

# 生产安装
pip install -e ".[prod]"
```

#### 2. 验证安装

```bash
python -c "from nyxai.api.main import app; print('✓ 安装成功')"
```

---

## 配置说明

### 配置文件

NyxAI 使用环境变量进行配置，支持以下配置文件：

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `.env.local` | 本地开发配置 | 最高 |
| `.env` | 通用配置 | 中 |
| 系统环境变量 | 生产环境配置 | 最低 |

### 核心配置项

#### 应用基础配置

```bash
# 运行环境: development, production
NYX_ENV=development

# 调试模式: true, false
NYX_DEBUG=true

# 密钥（生产环境必须修改）
NYX_SECRET_KEY=your-secret-key
```

#### 数据库配置

**嵌入式模式（默认）**

```bash
# SQLite 数据库
NYX_DB_URL=sqlite+aiosqlite:///./data/nyxai.db
NYX_DB_ECHO=false
```

**PostgreSQL 模式**

```bash
# PostgreSQL 数据库
NYX_DB_URL=postgresql+asyncpg://user:password@localhost:5432/nyxai
NYX_DB_POOL_SIZE=10
NYX_DB_MAX_OVERFLOW=20
```

#### 向量数据库配置

```bash
# 启用嵌入式向量数据库
NYX_VECTOR_ENABLED=true
NYX_VECTOR_PERSIST_DIRECTORY=./data/vector_db
NYX_VECTOR_COLLECTION_NAME=incidents
NYX_VECTOR_SIMILARITY_THRESHOLD=0.7
NYX_VECTOR_MAX_RESULTS=5
```

#### LLM 配置

```bash
# OpenAI
NYX_LLM_PROVIDER=openai
NYX_LLM_API_KEY=sk-...
NYX_LLM_MODEL=gpt-4

# 或 Anthropic
NYX_LLM_PROVIDER=anthropic
NYX_LLM_API_KEY=sk-ant-...
NYX_LLM_MODEL=claude-3-opus-20240229
```

#### Prometheus 配置（可选）

```bash
NYX_PROM_URL=http://localhost:9090
```

---

## 启动方式

### 方式一：开发脚本启动

#### Python 脚本（跨平台）

```bash
# 基础启动
python scripts/dev-start.py

# 指定端口
python scripts/dev-start.py --port 8080

# 启用自动重载（开发推荐）
python scripts/dev-start.py --reload

# 完整参数
python scripts/dev-start.py --host 0.0.0.0 --port 8000 --reload
```

#### Windows 批处理脚本

```bash
# 基础启动
scripts\dev-start.bat

# 指定端口
scripts\dev-start.bat 8080

# 启用自动重载
scripts\dev-start.bat --reload
```

#### PowerShell 脚本

```powershell
# 基础启动
.\scripts\dev-start.ps1

# 指定端口
.\scripts\dev-start.ps1 -Port 8080

# 启用自动重载
.\scripts\dev-start.ps1 -Reload
```

### 方式二：直接启动

```bash
# 设置环境变量后启动
export NYX_ENV=development
export NYX_DB_URL=sqlite+aiosqlite:///./data/nyxai.db
export NYX_VECTOR_ENABLED=true

# 使用 uvicorn 启动
uvicorn nyxai.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方式三：Docker 启动

#### 嵌入式模式（推荐用于测试）

```bash
# 启动
 docker-compose -f docker-compose.embedded.yml up -d

# 查看日志
docker-compose -f docker-compose.embedded.yml logs -f

# 停止
docker-compose -f docker-compose.embedded.yml down
```

#### 完整模式（生产环境）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## API 使用

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API 文档**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 健康检查

```bash
curl http://localhost:8000/health
```

响应：

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 核心 API 端点

#### 1. 异常检测

**提交异常**

```bash
curl -X POST http://localhost:8000/api/v1/anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "cpu_usage",
    "metric_labels": {"service": "user-service"},
    "value": 95.5,
    "expected_value": 60.0,
    "severity": "high",
    "algorithm": "isolation_forest"
  }'
```

**查询异常列表**

```bash
curl "http://localhost:8000/api/v1/anomalies?status=detected&limit=10"
```

**获取异常详情**

```bash
curl http://localhost:8000/api/v1/anomalies/{anomaly_id}
```

#### 2. 根因分析

**执行根因分析**

```bash
curl -X POST http://localhost:8000/api/v1/rca/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "anomaly_id": "550e8400-e29b-41d4-a716-446655440000",
    "include_topology": true,
    "include_attribution": true
  }'
```

**获取分析结果**

```bash
curl http://localhost:8000/api/v1/rca/results/{analysis_id}
```

#### 3. 恢复操作

**执行恢复操作**

```bash
curl -X POST http://localhost:8000/api/v1/recovery/execute \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy": "restart_service",
    "parameters": {
      "service_name": "user-service"
    }
  }'
```

**获取恢复策略列表**

```bash
curl http://localhost:8000/api/v1/recovery/strategies
```

#### 4. 指标查询

**即时查询**

```bash
curl "http://localhost:8000/api/v1/metrics/query?query=cpu_usage_percent"
```

**范围查询**

```bash
curl "http://localhost:8000/api/v1/metrics/query_range?query=cpu_usage_percent&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z&step=1h"
```

---

## 核心功能

### 1. 异常检测

NyxAI 支持多种异常检测算法：

- **Isolation Forest**: 基于随机划分的异常检测
- **Prophet**: 时间序列预测和异常检测
- **Statistical**: 基于统计阈值的检测
- **Ensemble**: 集成多种算法的结果

### 2. 根因分析

- **拓扑分析**: 基于服务依赖图定位根因
- **维度归因**: 分析异常的多维属性
- **LLM 辅助**: 使用大语言模型生成分析报告

### 3. 自动恢复

- **策略管理**: 定义和管理恢复策略
- **风险评估**: 评估恢复操作的风险
- **执行器**: 安全执行恢复操作
- **回滚支持**: 支持操作回滚

### 4. 知识库

- **事件存储**: 存储历史异常和恢复记录
- **向量搜索**: 基于相似度搜索相关事件
- **经验学习**: 从历史事件中学习恢复策略

---

## 故障排查

### 常见问题

#### 1. 启动失败

**问题**: `ImportError: No module named 'nyxai'`

**解决**:

```bash
# 确保在项目根目录
pip install -e .
export PYTHONPATH=./src:$PYTHONPATH
```

#### 2. 数据库连接失败

**问题**: `sqlalchemy.exc.OperationalError`

**解决**:

```bash
# 检查数据库目录是否存在
mkdir -p ./data

# 检查数据库 URL 配置
export NYX_DB_URL=sqlite+aiosqlite:///./data/nyxai.db
```

#### 3. 向量数据库错误

**问题**: `chromadb.errors.InvalidCollectionException`

**解决**:

```bash
# 删除向量数据库目录重新初始化
rm -rf ./data/vector_db
```

#### 4. LLM API 错误

**问题**: `openai.error.AuthenticationError`

**解决**:

```bash
# 检查 API Key 配置
export NYX_LLM_API_KEY=your-api-key
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/nyxai.log

# 查看错误日志
tail -f logs/error.log

# Docker 日志
docker-compose logs -f nyxai
```

### 调试模式

```bash
# 启用调试模式
export NYX_DEBUG=true
export NYX_LOG_LEVEL=DEBUG

# 启动服务
python scripts/dev-start.py
```

---

## 数据备份

### SQLite 数据库备份

```bash
# 备份
cp ./data/nyxai.db ./data/nyxai.db.backup

# 恢复
cp ./data/nyxai.db.backup ./data/nyxai.db
```

### 向量数据库备份

```bash
# 备份
tar czf vector_db_backup.tar.gz ./data/vector_db

# 恢复
tar xzf vector_db_backup.tar.gz
```

### Docker 卷备份

```bash
# 备份
docker run --rm -v nyxai_nyxai_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/nyxai-data.tar.gz -C /data .

# 恢复
docker run --rm -v nyxai_nyxai_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/nyxai-data.tar.gz -C /data
```

---

## 开发指南

### 项目结构

```
nyxai/
├── src/nyxai/           # 核心源代码
│   ├── api/            # API 路由和模型
│   ├── detection/      # 异常检测引擎
│   ├── rca/            # 根因分析
│   ├── recovery/       # 自动恢复
│   ├── knowledge_base/ # 知识库
│   ├── storage/        # 数据存储
│   └── llm/            # LLM 提供商
├── tests/              # 测试代码
├── scripts/            # 启动脚本
├── docs/               # 文档
└── deployments/        # 部署配置
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit

# 运行集成测试
pytest tests/integration

# 带覆盖率报告
pytest --cov=nyxai --cov-report=html
```

### 代码规范

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 类型检查
mypy src/nyxai
```

---

## 更多信息

- **GitHub**: https://github.com/your-org/nyxai
- **文档**: http://localhost:8000/docs (启动后)
- **Issue**: https://github.com/your-org/nyxai/issues

---

*最后更新: 2024-01-15*
