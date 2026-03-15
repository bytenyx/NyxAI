# Tasks

## Phase 1: 项目初始化

- [x] Task 1: 创建 React + TypeScript + Vite 项目
  - [x] SubTask 1.1: 使用 Vite 初始化项目 (frontend/)
  - [x] SubTask 1.2: 安装 Ant Design 和相关依赖
  - [x] SubTask 1.3: 配置 ESLint 和 Prettier
  - [x] SubTask 1.4: 配置 TypeScript 路径别名
  - [x] SubTask 1.5: 创建项目目录结构

- [x] Task 2: 配置基础工具和样式
  - [x] SubTask 2.1: 配置 Ant Design 主题定制
  - [x] SubTask 2.2: 创建全局样式文件
  - [x] SubTask 2.3: 配置 Axios HTTP 客户端
  - [x] SubTask 2.4: 配置 React Router

## Phase 2: 核心功能实现

- [x] Task 3: 实现认证模块
  - [x] SubTask 3.1: 创建登录页面组件
  - [x] SubTask 3.2: 实现认证状态管理 (Context/Redux)
  - [x] SubTask 3.3: 实现登录 API 集成
  - [x] SubTask 3.4: 实现路由守卫和权限控制
  - [x] SubTask 3.5: 实现登出功能

- [x] Task 4: 实现布局组件
  - [x] SubTask 4.1: 创建主布局组件 (侧边栏 + 头部 + 内容区)
  - [x] SubTask 4.2: 实现侧边栏菜单导航
  - [x] SubTask 4.3: 实现面包屑导航
  - [x] SubTask 4.4: 实现用户头像和下拉菜单
  - [x] SubTask 4.5: 实现响应式布局适配

- [x] Task 5: 实现仪表盘页面
  - [x] SubTask 5.1: 创建统计卡片组件
  - [x] SubTask 5.2: 集成 ECharts/Ant Design Charts 展示趋势图
  - [x] SubTask 5.3: 实现最近异常事件列表
  - [x] SubTask 5.4: 集成 WebSocket 实时数据更新
  - [x] SubTask 5.5: 实现数据自动刷新

- [x] Task 6: 实现指标监控页面
  - [x] SubTask 6.1: 创建指标查询表单
  - [x] SubTask 6.2: 实现指标图表展示组件
  - [x] SubTask 6.3: 支持时间范围选择器
  - [x] SubTask 6.4: 支持自定义 PromQL 查询
  - [x] SubTask 6.5: 实现图表导出功能

- [x] Task 7: 实现异常管理页面
  - [x] SubTask 7.1: 创建异常列表表格组件
  - [x] SubTask 7.2: 实现分页和筛选功能
  - [x] SubTask 7.3: 创建异常详情抽屉/弹窗
  - [x] SubTask 7.4: 实现异常状态管理操作
  - [x] SubTask 7.5: 集成相关指标展示

- [x] Task 8: 实现根因分析展示页面
  - [x] SubTask 8.1: 创建服务拓扑图可视化组件
  - [x] SubTask 8.2: 实现故障传播路径展示
  - [x] SubTask 8.3: 实现维度归因分析展示
  - [x] SubTask 8.4: 展示 LLM 分析结果
  - [x] SubTask 8.5: 支持历史 RCA 记录查看

- [x] Task 9: 实现恢复操作管理页面
  - [x] SubTask 9.1: 创建恢复策略列表
  - [x] SubTask 9.2: 实现恢复操作执行界面
  - [x] SubTask 9.3: 展示恢复执行进度和日志
  - [x] SubTask 9.4: 实现审批工作流界面
  - [x] SubTask 9.5: 展示恢复历史记录

- [x] Task 10: 实现系统配置页面
  - [x] SubTask 10.1: 创建通用设置表单
  - [x] SubTask 10.2: 实现用户管理表格
  - [x] SubTask 10.3: 实现角色权限配置
  - [x] SubTask 10.4: 实现通知配置

## Phase 3: 完善与优化

- [x] Task 11: 实现 WebSocket 实时通信
  - [x] SubTask 11.1: 创建 WebSocket 连接管理
  - [x] SubTask 11.2: 实现消息订阅和分发
  - [x] SubTask 11.3: 实现断线重连机制
  - [x] SubTask 11.4: 集成通知提醒组件

- [x] Task 12: 优化用户体验
  - [x] SubTask 12.1: 实现页面加载状态
  - [x] SubTask 12.2: 实现错误处理和友好提示
  - [x] SubTask 12.3: 实现空状态展示
  - [x] SubTask 12.4: 优化移动端适配
  - [x] SubTask 12.5: 实现暗黑模式支持

- [x] Task 13: 构建和部署配置
  - [x] SubTask 13.1: 配置生产环境构建
  - [x] SubTask 13.2: 更新 Docker 配置支持前端
  - [x] SubTask 13.3: 更新 Nginx 配置
  - [x] SubTask 13.4: 更新 CI/CD 流水线

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 2
- Task 4 依赖 Task 3
- Task 5 依赖 Task 4
- Task 6 依赖 Task 4
- Task 7 依赖 Task 4
- Task 8 依赖 Task 4
- Task 9 依赖 Task 4
- Task 10 依赖 Task 4
- Task 11 依赖 Task 5
- Task 12 依赖 Task 5, Task 6, Task 7
- Task 13 依赖 Task 1
