# 变更日志

所有重要的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-04-11

### Added

#### Web 前端
- feat(frontend): Streamlit 多页面应用框架
- feat(frontend): 主页、分析、配置、历史四个页面
- feat(frontend): K线图、MACD、RSI、雷达图、仪表盘图表组件
- feat(frontend): 异步 HTTP API 客户端
- feat(frontend): 侧边栏股票搜索与选择

#### AI 增强分析
- feat(ai): OpenAI 协议适配器 - 支持所有 OpenAI 兼容 API
- feat(ai): Anthropic 协议适配器 - 支持 Claude 系列模型
- feat(ai): AI 分析增强模式 - 基本面/技术面/综合分析

#### 测试覆盖率提升
- test: OpenAI Provider 覆盖率 60.27% → 100%
- test: Anthropic Provider 覆盖率 62.96% → 96.30%
- test: API Config 覆盖率 37.01% → 97.64%
- test: AKShare Client 覆盖率 39.30% → 84.08%
- test: Database 覆盖率 52.94% → 100%
- test: 总覆盖率 80.03% → 86.71%

### Changed

#### 架构优化
- refactor: Mock 策略优化 - Mock 外部依赖，测试内部逻辑
- refactor: FastAPI 依赖注入测试 - dependency_overrides
- refactor: 第三方库 Mock 方案

#### 文档与工具
- docs: 更新 README.md 为 v1.1
- docs: 添加前端使用说明
- chore: run_frontend.sh → run_frontend.py (Python 统一管理)

### Fixed

- fix: OpenAI Provider 测试覆盖率不足
- fix: Anthropic Provider 测试覆盖率不足
- fix: API Config 依赖注入测试问题
- fix: AKShare Client 网络依赖测试问题
- fix: Series.fillna 废弃警告

### Security

- feat(core): 安全模块增强
- feat(core): API Key 加密存储

---

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
