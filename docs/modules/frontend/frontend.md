# Frontend 模块文档

> **模块路径**: `frontend/`  
> **功能**: Streamlit Web 前端界面  
> **版本**: v1.1.0  
> **更新日期**: 2026-04-11

---

## 📋 模块列表

| 文件/目录 | 功能 | 状态 |
|-----------|------|------|
| `app.py` | 主页应用入口 | ✅ |
| `pages/` | 多页面目录 | ✅ |
| `components/` | 可复用UI组件 | ✅ |
| `utils/` | 前端工具函数 | ✅ |

---

## 🏗️ 架构设计

### 多页面结构

```
frontend/
├── app.py              # 主页 - 系统概览
├── pages/
│   ├── 1_Analysis.py       # 股票分析页面
│   ├── 2_Configuration.py  # API配置页面
│   └── 3_History.py        # 历史记录页面
├── components/
│   ├── charts.py       # 图表组件（K线、MACD、RSI）
│   ├── tables.py       # 表格组件
│   └── sidebar.py      # 侧边栏组件
└── utils/
    └── api_client.py   # 后端API客户端
```

---

## 📊 主要功能

### 1. 主页 (app.py)

**功能**:
- 系统概览仪表盘
- 快速分析入口
- 最近分析记录
- 系统状态展示

### 2. 分析页面 (1_Analysis.py)

**功能**:
- 股票代码输入
- 分析类型选择（长期/短期/综合）
- 实时分析结果展示
- K线图、MACD、RSI可视化
- 综合评分仪表盘
- 投资建议卡片

**图表组件**:
- K线图 (Candlestick)
- MACD指标图
- RSI指标图
- 雷达图（多维评分）
- 仪表盘（综合评分）

### 3. 配置页面 (2_Configuration.py)

**功能**:
- OpenAI API配置
- Anthropic API配置
- Tushare Token配置
- 默认分析设置
- 飞书推送配置（v1.2）

### 4. 历史页面 (3_History.py)

**功能**:
- 分析历史列表
- 报告详情查看
- 历史记录搜索
- 报告导出下载

---

## 🔧 API 客户端

### api_client.py

**核心类**: `APIClient`

**功能**:
- 异步HTTP请求
- 自动重试机制（指数退避）
- 超时配置
- 错误处理

**配置项**:
```python
api_timeout: int = 30        # 请求超时（秒）
api_max_retries: int = 3     # 最大重试次数
api_retry_delay: float = 1.0 # 重试延迟（秒）
```

**使用示例**:
```python
from frontend.utils.api_client import get_api_client

client = get_api_client()

# 获取股票信息
stock_info = await client.get(f"/api/v1/stock/{stock_code}")

# 执行分析
result = await client.post("/api/v1/analysis", data={
    "stock_code": "600276.SH",
    "analysis_type": "both"
})
```

---

## 📈 图表组件

### charts.py

**可用图表**:

| 函数 | 功能 | 参数 |
|------|------|------|
| `create_candlestick_chart()` | K线图 | quotes: list[DailyQuote] |
| `create_macd_chart()` | MACD指标 | macd_data: dict |
| `create_rsi_chart()` | RSI指标 | rsi_data: dict |
| `create_radar_chart()` | 雷达图 | scores: dict |
| `create_gauge_chart()` | 仪表盘 | score: float |

**示例**:
```python
from frontend.components.charts import create_candlestick_chart

fig = create_candlestick_chart(quotes)
st.plotly_chart(fig, use_container_width=True)
```

---

## 🚀 启动方式

### 开发模式

```bash
# 方式1: Makefile命令
make frontend

# 方式2: 直接运行
streamlit run frontend/app.py

# 方式3: 指定端口
streamlit run frontend/app.py --server.port 8501
```

### Docker模式

```bash
make docker
# 前端地址: http://localhost:8501
```

---

## ⚙️ 配置说明

### 环境变量

```bash
# 后端API地址（默认）
BACKEND_URL=http://localhost:8000

# Streamlit配置
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Streamlit配置文件

```toml
# .streamlit/config.toml
[server]
port = 8501
address = "0.0.0.0"
headless = true

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## 📝 开发规范

### 页面命名规则

```
{序号}_{页面名}.py

序号：决定页面顺序
页面名：英文，首字母大写
```

### 组件开发规范

1. **单一职责**: 每个组件只负责一个功能
2. **参数验证**: 使用类型注解
3. **错误处理**: 捕获并展示用户友好错误
4. **响应式布局**: 使用 `use_container_width=True`

---

## 🔄 版本规划

### v1.1 (当前)
- ✅ Streamlit多页面应用
- ✅ 基础图表组件
- ✅ API客户端
- ✅ 配置管理

### v1.2 (计划)
- 🚧 Vue.js前端重构
- 🚧 用户认证界面
- 🚧 高级图表功能
- 🚧 移动端适配

---

## 📚 相关文档

- **[README.md](../../README.md)** - 项目说明
- **[USER_GUIDE.md](../USER_GUIDE.md)** - 用户手册
- **[api.md](../api/api.md)** - API文档
- **[frontend/README.md](../../frontend/README.md)** - 前端使用说明

---

*文档版本: v1.1.0 | 最后更新: 2026-04-11*
