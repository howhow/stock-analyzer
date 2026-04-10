# Stock Analyzer 模块文档索引

> **版本**: v1.1.0  
> **更新日期**: 2026-04-11

---

## 📚 模块列表

| 模块 | 文档 | 功能 | 状态 |
|------|------|------|------|
| **core** | [core.md](./core/core.md) | 核心基础设施 | ✅ |
| **data** | [data.md](./data/data.md) | 数据获取与处理 | ✅ |
| **analysis** | [analysis.md](./analysis/analysis.md) | 股票分析引擎 | ✅ |
| **report** | [report.md](./report/report.md) | 报告生成与管理 | ✅ |
| **api** | [api.md](./api/api.md) | Web API 接口 | ✅ |
| **frontend** | [frontend.md](./frontend/frontend.md) | Streamlit Web 前端 | ✅ NEW |
| **ai** | [ai.md](./ai/ai.md) | AI协议适配器 | ✅ NEW |
| **tasks** | [tasks.md](./tasks/tasks.md) | 异步任务处理 | ✅ |
| **models** | [models.md](./models/models.md) | 数据模型定义 | ✅ |
| **utils** | [utils.md](./utils/utils.md) | 工具函数与日志 | ✅ |

---

## 🏗️ 架构分层

```
┌─────────────────────────────────────┐
│         Frontend Layer              │  frontend/
│         (Streamlit Pages)           │
├─────────────────────────────────────┤
│            API Layer                │  app/api/
│         (FastAPI Routes)            │
├─────────────────────────────────────┤
│         Analysis Layer              │  app/analysis/
│    (SystemAnalyzer, Indicators)     │
│              + AI Layer             │  app/ai/
│      (OpenAI, Anthropic Provider)   │
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

### 前端模块 ✨ NEW

- **[frontend.md](./frontend/frontend.md)** - Streamlit多页面应用、图表组件、API客户端

### AI模块 ✨ NEW

- **[ai.md](./ai/ai.md)** - OpenAI/Anthropic协议适配器、工厂模式、配额管理

### 核心模块

- **[core.md](./core/core.md)** - 缓存、熔断器、限流器、分布式锁、安全模块
- **[data.md](./data/data.md)** - 数据源、数据协调器、健康检查

### 业务模块

- **[analysis.md](./analysis/analysis.md)** - 分析引擎、技术指标、评分系统
- **[report.md](./report/report.md)** - HTML/Markdown 报告生成

### 服务模块

- **[api.md](./api/api.md)** - REST API 接口、认证授权、限流
- **[tasks.md](./tasks/tasks.md)** - Celery 异步任务、死信队列

### 基础模块

- **[models.md](./models/models.md)** - 数据模型、类型定义
- **[utils.md](./utils/utils.md)** - 日志系统、字段映射、工具函数

---

## 🔗 相关文档

- **README.md** - 项目说明
- **docs/USER_GUIDE.md** - 用户手册
- **docs/CHANGELOG.md** - 更新日志

---

## 📊 模块依赖关系

```
frontend → api → analysis → data → core
            ↓       ↓         ↓       ↓
          models  models + ai models  utils
            ↓       ↓
          report  report
```

**说明**:
- Frontend 依赖 API
- API 依赖 Analysis 和 Data
- Analysis 依赖 Data、Core 和 AI
- Data 依赖 Core
- Core 依赖 Utils
- Report 依赖 Models

---

## 🎯 开发指南

### 新增模块

1. 在 `app/` 或 `frontend/` 下创建模块目录
2. 编写模块代码
3. 创建 `docs/modules/<模块名>/<模块名>.md` 文档
4. 更新此索引文件

### 模块文档规范

每个模块文档应包含：
1. 模块列表
2. 架构设计
3. 核心类/函数说明
4. 使用示例
5. 配置说明
6. 版本规划

---

## ✨ v1.1.0 新增模块

### Frontend 模块

**路径**: `frontend/`

**核心功能**:
- Streamlit多页面应用
- K线图、MACD、RSI可视化
- API配置管理
- 异步HTTP客户端

**文档**: [frontend.md](./frontend/frontend.md)

### AI 模块

**路径**: `app/ai/`

**核心功能**:
- OpenAI协议适配器（兼容5+模型）
- Anthropic协议适配器（Claude系列）
- 工厂模式
- 自动重试机制

**文档**: [ai.md](./ai/ai.md)

---

*文档版本: v1.1.0 | 最后更新: 2026-04-11*
