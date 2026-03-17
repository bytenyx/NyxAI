# NyxAI 项目简化 - 验证清单

- [ ] 检查 1：pyproject.toml 中已移除 Redis 依赖
- [ ] 检查 2：config.py 中已移除 RedisSettings 类
- [ ] 检查 3：config.py 中默认数据库配置使用 SQLite
- [ ] 检查 4：storage/cache.py 中已实现内存缓存替代 Redis
- [ ] 检查 5：Celery 配置已修改为使用内存或文件系统
- [ ] 检查 6：向量数据库默认使用 Chroma
- [ ] 检查 7：系统能在没有 Redis 的情况下正常启动
- [ ] 检查 8：系统能在没有 PostgreSQL 的情况下正常启动
- [ ] 检查 9：所有系统功能正常工作
- [ ] 检查 10：系统启动时间不超过 10 秒
- [ ] 检查 11：内存使用不超过 512MB
- [ ] 检查 12：向量搜索功能正常工作