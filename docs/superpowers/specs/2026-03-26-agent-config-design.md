# Agent 在线配置系统设计文档

## 概述

本设计文档描述了 Agent 在线配置系统的实现方案，支持通过 Web UI 界面动态配置每个 Agent 的 system prompt 和可使用的 skill 列表。

## 背景

当前系统中，Agent 的 prompt 是硬编码在代码中的（如 `diagnosis.py` 中的 `system_prompt` 变量），skill 的可用性也是固定的。这导致：

1. 修改 prompt 需要修改代码并重新部署
2. 无法针对不同场景灵活调整 Agent 行为
3. 缺乏配置版本管理和回滚能力

## 目标

- 支持通过 Web UI 动态配置每个 Agent 的 system prompt
- 支持为每个 Agent 独立配置可用的 skill 列表
- 配置存储在数据库中，支持版本历史和回滚
- 配置修改后，Agent 在下次执行时自动生效

## 数据模型

### agent_configs 表

存储每个 Agent 类型的激活配置。

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| agent_type | String | Agent 类型（investigation/diagnosis/recovery/orchestrator） |
| name | String | 配置名称 |
| system_prompt | Text | Agent 的系统提示词 |
| allowed_skills | JSON | 可用技能列表，如 `["brainstorming", "systematic-debugging"]` |
| is_active | Boolean | 是否为激活配置 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

约束：每个 `agent_type` 只能有一个 `is_active=True` 的配置。

### agent_config_versions 表

存储配置的版本历史，支持回滚。

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| config_id | UUID | 外键，关联 agent_configs.id |
| version | Integer | 版本号，自动递增 |
| system_prompt | Text | 该版本的系统提示词快照 |
| allowed_skills | JSON | 该版本的技能列表快照 |
| changed_by | String | 修改者标识 |
| change_reason | String | 变更原因描述 |
| created_at | DateTime | 版本创建时间 |

## API 设计

### 配置管理 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agent-configs` | GET | 获取所有 Agent 配置列表 |
| `/api/agent-configs/{agent_type}` | GET | 获取指定类型 Agent 的激活配置 |
| `/api/agent-configs` | POST | 创建新配置 |
| `/api/agent-configs/{id}` | PUT | 更新配置（自动创建版本） |
| `/api/agent-configs/{id}` | DELETE | 删除配置 |
| `/api/agent-configs/{id}/activate` | POST | 激活指定配置 |
| `/api/agent-configs/{id}/versions` | GET | 获取配置版本历史 |
| `/api/agent-configs/{id}/rollback/{version}` | POST | 回滚到指定版本 |

### 技能查询 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/skills` | GET | 获取所有可用技能列表（从 SkillRegistry 获取） |

### API 请求/响应示例

**GET /api/agent-configs**
```json
[
  {
    "id": "uuid-1",
    "agent_type": "diagnosis",
    "name": "默认诊断配置",
    "system_prompt": "你是一个根因分析专家...",
    "allowed_skills": ["brainstorming", "systematic-debugging"],
    "is_active": true,
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:00:00Z"
  }
]
```

**POST /api/agent-configs**
```json
{
  "agent_type": "diagnosis",
  "name": "增强诊断配置",
  "system_prompt": "你是一个高级根因分析专家...",
  "allowed_skills": ["brainstorming", "systematic-debugging", "verification-before-completion"]
}
```

**PUT /api/agent-configs/{id}**
```json
{
  "system_prompt": "更新后的提示词...",
  "allowed_skills": ["brainstorming"],
  "change_reason": "优化诊断准确性"
}
```

## 核心流程

### 配置加载流程

```
1. Agent 初始化时，注入 AgentConfigRepository
2. Agent.execute() 调用前，从数据库加载该 agent_type 的激活配置
3. 如果存在配置，使用配置中的 system_prompt 和 allowed_skills
4. 如果不存在配置，使用代码中的默认值（向后兼容）
5. 调用 build_skill_prompt() 构建技能提示
```

### 配置更新流程

```
1. 用户通过 Web UI 修改配置
2. 后端接收 PUT 请求
3. 将当前配置快照保存到 agent_config_versions 表
4. 更新 agent_configs 表中的记录
5. Agent 下次执行时自动加载新配置
```

### 配置回滚流程

```
1. 用户选择要回滚的版本
2. 后端从 agent_config_versions 表获取历史快照
3. 创建新版本记录（当前状态）
4. 将历史版本的配置应用到 agent_configs 表
5. 返回成功响应
```

## 文件结构变更

### 后端新增文件

```
backend/app/
├── models/
│   └── agent_config.py          # AgentConfig, AgentConfigVersion 数据模型
├── storage/repositories/
│   └── agent_config_repo.py     # AgentConfigRepository 仓储类
├── api/
│   └── agent_configs.py         # 配置管理 API 路由
```

### 后端修改文件

```
backend/app/
├── storage/
│   └── models.py                # 添加 SQLAlchemy 模型定义
├── agents/
│   ├── base.py                  # 添加配置加载逻辑
│   ├── diagnosis.py             # 移除硬编码 prompt，使用配置
│   ├── investigation.py         # 移除硬编码 prompt，使用配置
│   └── recovery.py              # 移除硬编码 prompt，使用配置
├── main.py                      # 注册新路由
```

### 前端新增文件

```
frontend/src/
├── pages/
│   └── AgentConfigPage.tsx      # 配置管理页面
├── components/
│   └── AgentConfig/
│       ├── ConfigEditor.tsx     # 配置编辑器组件
│       ├── SkillSelector.tsx    # 技能选择器组件
│       └── VersionHistory.tsx   # 版本历史组件
├── services/
│   └── agentConfigApi.ts        # 配置 API 调用
├── types/
│   └── agentConfig.ts           # 配置类型定义
```

### 前端修改文件

```
frontend/src/
├── App.tsx                      # 添加配置页面路由
├── components/
│   └── Settings/
│       └── SettingsSidebar.tsx  # 添加配置管理入口
```

## 向后兼容

为确保现有功能不受影响：

1. 如果数据库中没有配置记录，Agent 使用代码中的默认 prompt
2. 首次启动时，自动从代码中提取默认配置并写入数据库
3. `allowed_skills` 为空时，Agent 不加载任何技能（当前行为）

## 测试策略

### 单元测试

- `test_agent_config_repo.py`: 测试配置仓储的 CRUD 操作
- `test_agent_configs_api.py`: 测试 API 端点
- `test_base_agent.py`: 测试配置加载逻辑

### 集成测试

- 测试配置修改后 Agent 行为变化
- 测试版本回滚功能
- 测试多 Agent 配置隔离

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 配置错误导致 Agent 行为异常 | 版本回滚功能；配置验证 |
| 数据库不可用时 Agent 无法工作 | 降级到代码默认配置 |
| 并发修改冲突 | 使用乐观锁或版本号校验 |

## 实现优先级

1. **P0 - 核心功能**
   - 数据模型和数据库迁移
   - AgentConfigRepository
   - 配置 API 端点
   - BaseAgent 配置加载逻辑

2. **P1 - 管理界面**
   - 前端配置管理页面
   - 技能选择器组件

3. **P2 - 增强功能**
   - 版本历史查看
   - 配置回滚功能
   - 配置导入/导出
