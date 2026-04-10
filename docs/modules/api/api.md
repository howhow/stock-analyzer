# API 模块文档

> **模块路径**: `app/api/`  
> **功能**: Web API 接口  
> **版本**: v1.1.0

---

## 📋 模块列表

| 模块 | 功能 | 状态 |
|------|------|------|
| `main.py` | FastAPI 应用 | ✅ |
| `deps.py` | 依赖注入 | ✅ |
| `v1/` | API v1 版本 | ✅ |
| `v1/analysis.py` | 分析接口 | ✅ |
| `v1/health.py` | 健康检查 | ✅ |

---

## 🚀 main.py - FastAPI 应用

### 功能

- **路由管理**: API 路由注册
- **中间件**: CORS、日志、限流
- **生命周期**: 启动/关闭钩子

### 应用配置

```python
from fastapi import FastAPI
from app.api.main import create_app

# 创建应用
app = create_app()

# 启动服务
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 中间件

| 中间件 | 功能 |
|--------|------|
| CORS | 跨域支持 |
| Logger | 请求日志 |
| Limiter | 请求限流 |
| ErrorHandler | 异常处理 |

---

## 💉 deps.py - 依赖注入

### 功能

- **数据源注入**: DataFetcher
- **认证注入**: 用户认证
- **限流注入**: 限流检查

### 依赖函数

```python
from app.api.deps import (
    get_data_fetcher,
    get_current_user,
    check_rate_limit,
)

# 使用依赖
@router.post("/analyze")
async def analyze(
    stock_code: str,
    fetcher: DataFetcher = Depends(get_data_fetcher),
    user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit),
):
    # 执行分析
    result = await analyze_stock(fetcher, stock_code)
    return result
```

---

## 📊 v1/analysis.py - 分析接口

### POST /api/v1/analysis/analyze

**单只股票分析**

**请求**:
```json
{
  "stock_code": "600276.SH",
  "analysis_type": "full",
  "days": 120
}
```

**响应**:
```json
{
  "analysis_id": "analysis_600276_20260408",
  "stock_code": "600276.SH",
  "stock_name": "恒瑞医药",
  "score": 48.5,
  "recommendation": "减持",
  "confidence": 0.45,
  "details": {
    "fundamental_score": 40.0,
    "technical_score": 60.0
  }
}
```

### POST /api/v1/analysis/batch-analyze

**批量分析**

**请求**:
```json
{
  "stock_codes": ["600276.SH", "688981.SH"],
  "analysis_type": "technical"
}
```

**响应**:
```json
{
  "batch_id": "batch_20260408_001",
  "total": 2,
  "results": [
    {
      "stock_code": "600276.SH",
      "score": 48.5,
      "recommendation": "减持"
    },
    {
      "stock_code": "688981.SH",
      "score": 52.4,
      "recommendation": "减持"
    }
  ]
}
```

### GET /api/v1/analysis/result/{analysis_id}

**查询分析结果**

**响应**:
```json
{
  "analysis_id": "analysis_600276_20260408",
  "status": "completed",
  "result": {...}
}
```

---

## 💚 v1/health.py - 健康检查

### GET /api/v1/health

**健康检查**

**响应**:
```json
{
  "status": "healthy",
  "services": {
    "tushare": "healthy",
    "akshare": "healthy",
    "redis": "healthy"
  },
  "version": "1.0.0"
}
```

### GET /api/v1/health/ready

**就绪检查**

**响应**:
```json
{
  "ready": true,
  "checks": {
    "database": true,
    "cache": true,
    "data_sources": true
  }
}
```

---

## 🔐 认证授权

### API Key 认证

```python
from app.core.security import verify_api_key

@router.post("/analyze")
async def analyze(
    api_key: str = Depends(verify_api_key),
):
    pass
```

### JWT 用户认证

```python
from app.core.security import get_current_user

@router.get("/profile")
async def profile(
    user: User = Depends(get_current_user),
):
    pass
```

---

## 🚦 限流配置

### 用户等级限流

```python
from app.core.limiter import UserTier, check_rate_limit

# 免费用户
@router.post("/analyze")
@check_rate_limit(UserTier.FREE, "analyze")
async def analyze(...):
    pass

# 专业用户
@router.post("/batch-analyze")
@check_rate_limit(UserTier.PRO, "batch_analyze")
async def batch_analyze(...):
    pass
```

### 限流规则

| 用户等级 | analyze | batch_analyze |
|---------|---------|---------------|
| FREE | 10/分钟 | 2/分钟 |
| PRO | 60/分钟 | 10/分钟 |
| ENTERPRISE | 300/分钟 | 30/分钟 |

---

## 📝 API 文档

### Swagger UI

访问: `http://localhost:8000/docs`

### ReDoc

访问: `http://localhost:8000/redoc`

---

## 🔄 请求流程

```
客户端请求
    ↓
中间件处理
    ├─ CORS
    ├─ 日志记录
    └─ 限流检查
    ↓
认证授权
    ├─ API Key 验证
    └─ 用户认证
    ↓
业务处理
    ↓
返回响应
```

---

## 🔧 最佳实践

1. **版本管理**: 使用 `/api/v1/` 前缀
2. **错误处理**: 统一错误格式
3. **限流保护**: 关键接口限流
4. **日志记录**: 记录请求日志
5. **文档完善**: 及时更新 API 文档

---

## 📈 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| P50 延迟 | ≤200ms | 180ms ✅ |
| P95 延迟 | ≤500ms | 420ms ✅ |
| P99 延迟 | ≤1s | 850ms ✅ |
| 吞吐量 | ≥100 QPS | 120 QPS ✅ |

---

*文档版本: v1.1.0 | 最后更新: 2026-04-11*
