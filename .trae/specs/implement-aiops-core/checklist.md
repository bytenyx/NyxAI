# Checklist

## Phase 1: 基础架构搭建

- [x] Python 项目核心文件已创建
  - [x] src/nyxai/__init__.py 存在且可导入
  - [x] src/nyxai/config.py 实现配置管理
  - [x] src/nyxai/utils.py 实现常用工具函数

- [x] 数据采集层已实现
  - [x] Prometheus 指标采集器可正常查询指标
  - [x] Loki 日志采集器可正常查询日志
  - [x] 事件采集器可将事件写入 PostgreSQL
  - [x] 数据预处理模块工作正常

- [x] 存储层已实现
  - [x] PostgreSQL 连接正常，可执行 CRUD 操作
  - [x] Redis 连接正常，可读写缓存
  - [x] Prometheus 查询客户端可执行 PromQL
  - [x] 数据库模型和表结构正确创建

- [x] 异常检测引擎基础已实现
  - [x] 统计检测引擎可检测 3-sigma 异常
  - [x] 检测器基类定义清晰，可扩展
  - [x] 异常事件模型可正确存储异常信息

- [x] API 层基础已实现
  - [x] FastAPI 应用可正常启动
  - [x] 健康检查端点返回正常
  - [x] 异常管理 API 可 CRUD 异常
  - [x] 指标查询 API 可查询 Prometheus 数据

- [x] Docker 开发环境已配置
  - [x] Dockerfile 可构建成功
  - [x] docker-compose.yml 可启动所有服务
  - [x] Prometheus 配置正确，可采集指标

## Phase 2: 核心引擎实现

- [x] 异常检测引擎已完善
  - [x] ML 检测引擎 (Isolation Forest) 工作正常 - src/nyxai/detection/engines/ml_detector.py
  - [x] ML 检测引擎 (LOF) 工作正常 - src/nyxai/detection/engines/ml_detector.py
  - [x] 动态阈值算法可自适应调整 - src/nyxai/detection/engines/adaptive_detector.py
  - [x] 分位数检测器可基于百分位数检测异常 - src/nyxai/detection/engines/adaptive_detector.py
  - [x] 季节性自适应检测器可处理周期性数据 - src/nyxai/detection/engines/adaptive_detector.py
  - [x] 集成检测器可综合多算法结果 - src/nyxai/detection/engines/ensemble_detector.py

- [x] 根因分析引擎已实现
  - [x] 服务拓扑图可正确构建 - src/nyxai/rca/topology/service_graph.py
  - [x] 服务节点可表示服务状态和指标
  - [x] 依赖边可表示服务间调用关系
  - [x] 故障传播分析可定位根因服务
  - [x] 上游/下游服务查询可获取依赖关系
  - [x] 关键路径分析可找出关键调用链
  - [x] 维度归因分析可定位异常维度 (src/nyxai/rca/attribution/dimension_attributor.py)

- [x] 自动恢复引擎已实现
  - [x] 策略管理可匹配和执行策略 - src/nyxai/recovery/strategies/
  - [x] 重启服务策略可处理内存泄漏等问题
  - [x] 扩容策略可处理高负载场景
  - [x] 清理缓存策略可处理缓存问题
  - [x] 熔断策略可处理级联故障
  - [x] 风险评估可正确评估操作风险 - src/nyxai/recovery/risk/assessor.py
  - [x] 风险评估考虑7个维度：服务关键性、操作影响、失败概率、回滚难度、影响范围、时间、依赖数
  - [x] 动作执行器可执行恢复动作 - src/nyxai/recovery/executor/executor.py
  - [x] 执行器支持dry-run模式和回滚

- [x] Agent 编排层已实现
  - [x] Agent 基类定义清晰 - src/nyxai/agents/base.py
  - [x] AgentContext 可在 Agent 间传递上下文
  - [x] AgentResult 可表示执行结果
  - [x] Monitor Agent 可检测异常并触发后续流程 - src/nyxai/agents/monitor.py
  - [x] Analyze Agent 可执行根因分析 - src/nyxai/agents/analyze.py
  - [x] Analyze Agent 支持拓扑分析和LLM分析
  - [x] Decide Agent 可做出恢复决策 - src/nyxai/agents/decide.py
  - [x] Decide Agent 集成知识库搜索
  - [x] Execute Agent 可执行恢复动作 - src/nyxai/agents/execute.py
  - [x] Execute Agent 支持审批工作流

- [x] LLM 集成已实现
  - [x] LLM Provider 抽象可切换不同模型 - src/nyxai/llm/providers/base.py
  - [x] OpenAI Provider 可调用 GPT 模型 - src/nyxai/llm/providers/openai_provider.py
  - [x] Anthropic Provider 可调用 Claude 模型 - src/nyxai/llm/providers/anthropic_provider.py
  - [x] 支持同步/异步调用和流式响应
  - [x] 根因分析提示词可生成有效分析 - src/nyxai/llm/prompts/rca_prompts.py
    - [x] 支持多种提示词模板 (standard, detailed, technical, executive)
    - [x] 支持中英文双语输出
    - [x] 集成维度归因分析上下文
    - [x] 集成服务拓扑上下文
    - [x] 结构化 JSON 输出格式
  - [ ] 工具调用框架可执行外部工具

- [x] 知识库已实现
  - [x] 故障知识库可存储和检索历史故障 - src/nyxai/knowledge_base/incident_kb.py
  - [x] 向量嵌入可生成事件向量表示
  - [x] 相似度检索可找到相似故障
  - [x] 支持标签搜索和服务搜索
  - [x] 支持 JSON 导入/导出

## Phase 3: 完善与部署

- [x] API 和 WebSocket 已完善
  - [x] 完整的 REST API 端点已实现
    - [x] 认证端点 - /api/v1/auth/*
    - [x] 异常管理端点 - /api/v1/anomalies/*
    - [x] 指标查询端点 - /api/v1/metrics/*
    - [x] 恢复动作端点 - /api/v1/recovery/*
    - [x] RCA 端点 - /api/v1/rca/*
  - [x] WebSocket 实时事件推送已实现 - /ws/events
    - [x] 支持多种事件类型：异常检测、恢复完成、RCA完成等
    - [x] 支持订阅/取消订阅特定事件类型
    - [x] 支持 ping/pong 心跳检测
  - [x] API 认证和授权机制已实现
    - [x] JWT Token 认证
    - [x] API Key 认证
    - [x] 基于角色的访问控制 (RBAC)
    - [x] 三种角色：Admin, Operator, Viewer

- [x] 测试已编写
  - [x] 单元测试已编写 - tests/unit/detection/
    - [x] test_statistical_detector.py - ThreeSigmaDetector 和 EWMADetector 测试
    - [x] test_anomaly_model.py - Anomaly 模型测试
  - [x] 集成测试目录已创建 - tests/integration/
  - [x] pytest fixtures 已配置 - tests/conftest.py
    - [x] sample_metric_data - 样本指标数据
    - [x] sample_metric_data_with_anomaly - 带异常的样本数据
    - [x] sample_anomaly_data - 样本异常数据
    - [x] sample_service_graph_data - 样本服务图数据
    - [x] mock_prometheus_response - Mock Prometheus 响应
    - [x] mock_loki_response - Mock Loki 响应
    - [x] sample_recovery_action - 样本恢复动作
    - [x] sample_incident_record - 样本故障记录

- [x] 部署配置已完成
  - [x] Kubernetes manifests 已编写 - k8s/base/
    - [x] namespace.yaml - 命名空间
    - [x] configmap.yaml - 配置映射
    - [x] secret.yaml - 密钥
    - [x] deployment.yaml - 部署
    - [x] service.yaml - 服务
    - [x] ingress.yaml - 入口
    - [x] rbac.yaml - RBAC 权限
    - [x] hpa.yaml - 水平自动扩缩容
    - [x] kustomization.yaml - Kustomize 配置
  - [x] CI/CD 流水线已配置 - .github/workflows/
    - [x] ci.yml - 持续集成
      - [x] Lint 检查 (Ruff, MyPy)
      - [x] 单元测试
      - [x] 代码覆盖率
      - [x] Docker 镜像构建
    - [x] cd.yml - 持续部署
      - [x] 发布到 GitHub Releases
      - [x] 部署到 Staging 环境
      - [x] 部署到 Production 环境
