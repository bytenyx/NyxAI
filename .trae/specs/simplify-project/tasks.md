# NyxAI 项目简化 - 实现计划

## [ ] 任务 1：修改 pyproject.toml，移除 Redis 依赖
- **优先级**：P0
- **依赖**：无
- **描述**：
  - 从 pyproject.toml 文件中移除 redis 依赖
  - 确保其他依赖保持不变
- **验收标准**：AC-2
- **测试要求**：
  - `programmatic` TR-1.1：pyproject.toml 文件中不再包含 redis 依赖
  - `programmatic` TR-1.2：使用 uv 工具能正常安装依赖
- **注意**：确保其他依赖项不受影响

## [ ] 任务 2：修改配置文件，移除 Redis 相关配置
- **优先级**：P0
- **依赖**：任务 1
- **描述**：
  - 修改 config.py 文件，移除 RedisSettings 类
  - 从 Settings 类中移除 redis 字段
  - 确保默认配置使用 SQLite
- **验收标准**：AC-1, AC-2
- **测试要求**：
  - `programmatic` TR-2.1：config.py 文件中不再包含 RedisSettings 类
  - `programmatic` TR-2.2：系统默认配置使用 SQLite
- **注意**：确保其他配置项不受影响

## [ ] 任务 3：修改缓存模块，使用内存缓存替代 Redis
- **优先级**：P0
- **依赖**：任务 2
- **描述**：
  - 修改 storage/cache.py 文件，实现内存缓存
  - 保持与原有缓存接口兼容
  - 移除 Redis 相关代码
- **验收标准**：AC-2
- **测试要求**：
  - `programmatic` TR-3.1：cache.py 文件中不再使用 Redis
  - `programmatic` TR-3.2：缓存功能正常工作
- **注意**：确保缓存接口保持不变，以便其他模块能正常使用

## [ ] 任务 4：修改 Celery 配置，使用内存或文件系统作为后端
- **优先级**：P0
- **依赖**：任务 2
- **描述**：
  - 修改 config.py 文件中的 CelerySettings 类
  - 将 broker_url 和 result_backend 改为使用内存或文件系统
- **验收标准**：AC-2
- **测试要求**：
  - `programmatic` TR-4.1：Celery 配置不再使用 Redis
  - `programmatic` TR-4.2：Celery 任务能正常执行
- **注意**：确保 Celery 能正常工作，即使没有 Redis

## [ ] 任务 5：确认向量数据库配置使用 Chroma
- **优先级**：P1
- **依赖**：无
- **描述**：
  - 检查并确认 vector_store.py 文件中的配置
  - 确保默认使用 Chroma 作为向量数据库
  - 移除对其他向量数据库的依赖
- **验收标准**：AC-3
- **测试要求**：
  - `programmatic` TR-5.1：向量数据库默认使用 Chroma
  - `programmatic` TR-5.2：向量搜索功能正常工作
- **注意**：确保 Chroma 配置正确，能正常存储和搜索向量

## [ ] 任务 6：修改数据库配置，确保 SQLite 作为默认选项
- **优先级**：P1
- **依赖**：任务 2
- **描述**：
  - 检查并确认 database.py 文件中的配置
  - 确保默认使用 SQLite 数据库
  - 确保 PostgreSQL 仍然可以作为选项
- **验收标准**：AC-1
- **测试要求**：
  - `programmatic` TR-6.1：默认数据库配置使用 SQLite
  - `programmatic` TR-6.2：系统能正常使用 SQLite 数据库
- **注意**：确保 PostgreSQL 作为可选配置仍然可用

## [ ] 任务 7：测试系统在简化配置下的运行
- **优先级**：P0
- **依赖**：任务 1-6
- **描述**：
  - 启动系统，确保能正常运行
  - 测试各种系统功能
  - 验证所有功能正常工作
- **验收标准**：AC-4
- **测试要求**：
  - `programmatic` TR-7.1：系统能正常启动
  - `programmatic` TR-7.2：所有系统功能正常工作
- **注意**：确保在没有 Redis 和 PostgreSQL 的情况下，系统能正常运行