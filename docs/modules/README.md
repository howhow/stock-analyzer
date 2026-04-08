# Stock Analyzer 模块文档索引

> **版本**: v1.0.0  
> **更新日期**: 2026-04-08

---

## 📚 模块列表

| 模块 | 文档 | 功能 | 状态 |
|------|------|------|------|
| **core** | [core.md](./core.md) | 核心基础设施 | ✅ |
| **data** | [data.md](./data.md) | 数据获取与处理 | ✅ |
| **analysis** | [analysis.md](./analysis.md) | 股票分析引擎 | ✅ |
| **report** | [report.md](./report.md) | 报告生成与管理 | ✅ |
| **api** | [api.md](./api.md) | Web API 接口 | ✅ |
| **tasks** | [tasks.md](./tasks.md) | 异步任务处理 | ✅ |
| **models** | [models.md](./models.md) | 数据模型定义 | ✅ |
| **utils** | [utils.md](./utils.md) | 工具函数与日志 | ✅ |

---

## 🏗️ 架构分层

```
┌─────────────────────────────────────┐
│            API Layer                │  app/api/
│         (FastAPI Routes)            │
├─────────────────────────────────────┤
│         Analysis Layer              │  app/analysis/
│    (SystemAnalyzer, Indicators)     │
├─────────────────────────────────────┤
│           Data Layer                │  app/data/
│  (TushareClient, AKShareClient)     │
├─────────────────────────────────────┤
│           Core Layer                │  app/core/
│  (Cache, CircuitBreaker, Limiter)   │
└─────────────────────────────────────┘
```

---

## 📖 快速导航

### 核心模块

- **[core.md](./core.md)** - 缓存、熔断器、限流器、分布式锁
- **[data.md](./data.md)** - 数据源、数据协调器、健康检查

### 业务模块

- **[analysis.md](./analysis.md)** - 分析引擎、技术指标、评分系统
- **[report.md](./report.md)** - HTML/Markdown 报告生成

### 服务模块

- **[api.md](./api.md)** - REST API 接口、认证授权、限流
- **[tasks.md](./tasks.md)** - Celery 异步任务、死信队列

### 基础模块

- **[models.md](./models.md)** - 数据模型、类型定义
- **[utils.md](./utils.md)** - 日志系统、字段映射、工具函数

---

## 🔗 相关文档

- **README.md** - 项目说明
- **docs/USER_GUIDE.md** - 用户手册
- **ARCHITECTURE_REVIEW.md** - 架构审查
- **docs/CHANGELOG.md** - 更新日志

---

## 📊 模块依赖关系

```
api → analysis → data → core
      ↓           ↓       ↓
    models     models   utils
      ↓           ↓
    report      report
```

**说明**:
- API 依赖 Analysis 和 Data
- Analysis 依赖 Data 和 Core
- Data 依赖 Core
- Core 依赖 Utils
- Report 依赖 Models

---

## 🎯 开发指南

### 新增模块

1. 在 `app/` 下创建模块目录
2. 编写模块代码
3. 创建 `docs/modules/<模块名>.md` 文档
4. 更新此索引文件

### 模块文档规范

每个模块文档应包含：
1. 模块列表
2. 核心类/函数说明
3. 使用示例
4. 最佳实践
5. 性能指标

---

*文档版本: v1.0 | 最后更新: 2026-04-08*
