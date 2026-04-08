# 变更日志

所有重要的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-04-06

### Added

#### P0 核心模块
- feat(core): 安全模块 - API Key + JWT 双认证、数据加密（PBKDF2）
- feat(core): 限流器 - 分级限流（IP/用户/全局）、滑动窗口算法、Lua 原子操作
- feat(core): 布隆过滤器 - MurmurHash3 双重哈希、防缓存穿透
- feat(core): 分布式锁 - 看门狗自动续期、可重入锁设计

#### P1 异步任务与监控
- feat(tasks): Celery 配置 - 定时任务、任务队列
- feat(tasks): 分析任务 - 异步分析、批量分析
- feat(tasks): 订阅任务 - 用户订阅管理
- feat(tasks): 清理任务 - 过期数据清理
- feat(tasks): 死信队列 - 失败任务处理
- feat(monitoring): Prometheus 指标 - 业务监控指标

#### 测试与工具
- feat(scripts): 全回归测试脚本 - 中芯国际 688981.SH
- feat(tests): 完整单元测试覆盖 - 536 passed, 81.08% coverage

### Changed
- refactor(core): datetime.utcnow() → datetime.now(datetime.UTC)
- refactor: 清理未使用导入 (F401)
- refactor: 完善类型注解 (mypy)

### Fixed
- fix: AsyncMock 导入问题
- fix: 测试用例 async 适配
- fix: E501 行长度超标
- fix: mypy/black/flake8 问题

### Security
- 安全模块支持 PBKDF2 密码哈希
- JWT 双 Token 机制（access + refresh）

---

## [0.1.0] - 2026-04-05

### Added
- feat(infra): 项目基础设施初始化
- feat(config): 配置管理模块（pydantic-settings）
- feat(models): 数据模型定义（股票、分析、报告）
- feat(api): FastAPI 框架搭建
- feat(core): 异常定义模块
- feat(utils): 工具函数（日志、计时、验证器）
- feat(tests): 单元测试框架
