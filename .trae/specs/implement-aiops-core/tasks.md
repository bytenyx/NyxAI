# Tasks

## Phase 1: 基础架构搭建

- [x] Task 1: 创建 Python 项目核心文件
  - [x] SubTask 1.1: 创建 src/nyxai/__init__.py
  - [x] SubTask 1.2: 创建 src/nyxai/config.py 配置管理
  - [x] SubTask 1.3: 创建 src/nyxai/utils.py 工具函数

- [x] Task 2: 实现数据采集层
  - [x] SubTask 2.1: 实现 Prometheus 指标采集器 (src/nyxai/collectors/metrics.py)
  - [x] SubTask 2.2: 实现 Loki 日志采集器 (src/nyxai/collectors/logs.py)
  - [x] SubTask 2.3: 实现事件采集器 (src/nyxai/collectors/events.py)
  - [x] SubTask 2.4: 实现数据预处理模块 (src/nyxai/collectors/preprocessing/)

- [x] Task 3: 实现存储层
  - [x] SubTask 3.1: 实现 PostgreSQL 数据库连接 (src/nyxai/storage/database.py)
  - [x] SubTask 3.2: 实现 Redis 缓存连接 (src/nyxai/storage/cache.py)
  - [x] SubTask 3.3: 实现 Prometheus 查询客户端 (src/nyxai/storage/prometheus_client.py)
  - [x] SubTask 3.4: 创建数据库模型和迁移脚本

- [x] Task 4: 实现异常检测引擎基础
  - [x] SubTask 4.1: 实现统计检测引擎 (src/nyxai/detection/engines/statistical_detector.py)
  - [x] SubTask 4.2: 实现检测器基类 (src/nyxai/detection/base.py)
  - [x] SubTask 4.3: 实现异常事件模型 (src/nyxai/detection/models/anomaly.py)

- [x] Task 5: 实现 API 层基础
  - [x] SubTask 5.1: 创建 FastAPI 应用入口 (src/nyxai/api/main.py)
  - [x] SubTask 5.2: 实现健康检查端点 (src/nyxai/api/routes/health.py)
  - [x] SubTask 5.3: 实现异常管理 API (src/nyxai/api/routes/anomalies.py)
  - [x] SubTask 5.4: 实现指标查询 API (src/nyxai/api/routes/metrics.py)

- [x] Task 6: 创建 Docker 开发环境
  - [x] SubTask 6.1: 编写 Dockerfile
  - [x] SubTask 6.2: 编写 docker-compose.yml (包含 Prometheus, PostgreSQL, Redis, Loki)
  - [x] SubTask 6.3: 编写 Prometheus 配置文件

## Phase 2: 核心引擎实现

- [x] Task 7: 完善异常检测引擎
  - [x] SubTask 7.1: 实现 ML 检测引擎 (Isolation Forest, LOF) - src/nyxai/detection/engines/ml_detector.py
  - [x] SubTask 7.2: 实现动态阈值算法 - src/nyxai/detection/engines/adaptive_detector.py
  - [x] SubTask 7.3: 实现集成检测器 - src/nyxai/detection/engines/ensemble_detector.py

- [x] Task 8: 实现根因分析引擎
  - [x] SubTask 8.1: 实现服务拓扑图 (src/nyxai/rca/topology/service_graph.py)
  - [x] SubTask 8.2: 实现故障传播分析
  - [ ] SubTask 8.3: 实现维度归因分析

- [x] Task 9: 实现自动恢复引擎
  - [x] SubTask 9.1: 实现策略管理 (src/nyxai/recovery/strategies/)
  - [x] SubTask 9.2: 实现风险评估 (src/nyxai/recovery/risk/assessor.py)
  - [x] SubTask 9.3: 实现动作执行器 (src/nyxai/recovery/executor/executor.py)

- [x] Task 10: 实现 Agent 编排层
  - [x] SubTask 10.1: 实现 Agent 基类 (src/nyxai/agents/base.py)
  - [x] SubTask 10.2: 实现 Monitor Agent (src/nyxai/agents/monitor.py)
  - [x] SubTask 10.3: 实现 Analyze Agent (src/nyxai/agents/analyze.py)
  - [x] SubTask 10.4: 实现 Decide Agent (src/nyxai/agents/decide.py)
  - [x] SubTask 10.5: 实现 Execute Agent (src/nyxai/agents/execute.py)

- [x] Task 11: 实现 LLM 集成
  - [x] SubTask 11.1: 实现 LLM Provider 抽象 (src/nyxai/llm/providers/)
  - [x] SubTask 11.2: 实现 OpenAI Provider (src/nyxai/llm/providers/openai_provider.py)
  - [x] SubTask 11.3: 实现 Anthropic Provider (src/nyxai/llm/providers/anthropic_provider.py)
  - [ ] SubTask 11.4: 实现根因分析提示词
  - [ ] SubTask 11.5: 实现工具调用框架

- [x] Task 12: 实现知识库
  - [x] SubTask 12.1: 实现故障知识库 (src/nyxai/knowledge_base/incident_kb.py)
  - [x] SubTask 12.2: 实现向量嵌入和检索

## Phase 3: 完善与部署

- [x] Task 13: 完善 API 和 WebSocket
  - [x] SubTask 13.1: 实现完整的 REST API - 异常、恢复、RCA、认证端点
  - [x] SubTask 13.2: 实现 WebSocket 实时事件推送 - /ws/events
  - [x] SubTask 13.3: 实现 API 认证和授权 - JWT + API Key

- [x] Task 14: 编写测试
  - [x] SubTask 14.1: 编写单元测试 - tests/unit/detection/
  - [x] SubTask 14.2: 编写集成测试 - tests/integration/
  - [x] SubTask 14.3: 配置 pytest 和测试 fixtures - tests/conftest.py

- [x] Task 15: 部署配置
  - [x] SubTask 15.1: 编写 Kubernetes manifests - k8s/base/
  - [x] SubTask 15.2: 配置 CI/CD - .github/workflows/

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 1
- Task 4 依赖 Task 1
- Task 5 依赖 Task 3
- Task 7 依赖 Task 4
- Task 8 依赖 Task 2, Task 3
- Task 9 依赖 Task 3
- Task 10 依赖 Task 4, Task 8, Task 9
- Task 11 依赖 Task 8
- Task 12 依赖 Task 3
- Task 13 依赖 Task 5, Task 10
- Task 14 依赖 Task 5, Task 7
- Task 15 依赖 Task 6
