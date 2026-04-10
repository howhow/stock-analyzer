# Stock Analyzer Frontend

Streamlit 前端界面，提供股票分析的 Web 交互界面。

## 快速启动

### 方式1: 使用 Makefile

```bash
# 启动后端（终端1）
make dev

# 启动前端（终端2）
make frontend
```

### 方式2: 使用启动脚本

```bash
# 先启动后端
make dev

# 运行前端启动脚本
./run_frontend.sh
```

### 方式3: 直接运行

```bash
# 激活虚拟环境
source local_venv/bin/activate

# 进入前端目录
cd frontend

# 启动 Streamlit
streamlit run app.py
```

## 访问地址

- **前端界面**: http://localhost:8501
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 目录结构

```
frontend/
├── __init__.py           # 模块初始化
├── app.py                # 主入口页面
├── pages/                # 多页面应用
│   ├── 1_📊_分析.py      # 股票分析页面
│   ├── 2_⚙️_配置.py      # AI 配置页面
│   └── 3_📋_历史.py      # 分析历史页面
├── components/           # 可复用组件
│   ├── __init__.py
│   ├── charts.py         # 图表组件
│   ├── tables.py         # 表格组件
│   └── sidebar.py        # 侧边栏组件
└── utils/                # 工具函数
    ├── __init__.py
    └── api_client.py     # API 客户端
```

## 功能页面

### 1. 主页 (app.py)

- 系统状态检查
- 快速分析入口
- 配置状态展示
- 功能介绍

### 2. 分析页面 (1_📊_分析.py)

- 股票代码输入
- 分析类型选择（综合/基本面/技术面）
- 分析模式选择（算法/AI）
- 结果展示：
  - 综合评分仪表盘
  - 能力雷达图
  - K线图 + 成交量
  - MACD/RSI 指标图
  - 投资建议

### 3. 配置页面 (2_⚙️_配置.py)

- OpenAI API 配置
- Anthropic API 配置
- 分析偏好设置
- API Key 加密存储

### 4. 历史页面 (3_📋_历史.py)

- 分析历史查询
- 筛选（股票代码、时间范围）
- 详情查看
- 数据导出

## 图表组件

### K线图

```python
from frontend.components.charts import create_candlestick_chart

fig = create_candlestick_chart(
    df,               # DataFrame with OHLCV
    title="K线图",
    show_volume=True,
    show_ma=True,
)
st.plotly_chart(fig)
```

### 技术指标图

```python
from frontend.components.charts import create_indicator_chart

fig = create_indicator_chart(df, indicator="MACD")
st.plotly_chart(fig)
```

### 评分仪表盘

```python
from frontend.components.charts import create_score_gauge

fig = create_score_gauge(score=75, title="综合评分")
st.plotly_chart(fig)
```

### 雷达图

```python
from frontend.components.charts import create_radar_chart

data = {"基本面": 80, "技术面": 70, "趋势": 65}
fig = create_radar_chart(data, title="能力雷达图")
st.plotly_chart(fig)
```

## API 客户端

```python
from frontend.utils.api_client import get_api_client

client = get_api_client()

# GET 请求
result = await client.get("/api/v1/config/user_id")

# POST 请求
result = await client.post("/api/v1/analysis/analyze", data={
    "stock_code": "600519.SH",
    "analysis_type": "both",
    "mode": "algorithm",
})
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| STREAMLIT_SERVER_PORT | 8501 | 前端端口 |
| STREAMLIT_SERVER_ADDRESS | 0.0.0.0 | 监听地址 |

## 依赖

- streamlit >= 1.32.0
- plotly >= 5.18.0
- httpx (已在后端依赖中)
- pandas (已在后端依赖中)

## 注意事项

1. **后端依赖**: 前端需要后端服务运行才能正常工作
2. **API Key 安全**: API Key 使用 AES-256 加密存储
3. **会话管理**: 使用 Streamlit session_state 管理用户状态

## 开发指南

### 添加新页面

1. 在 `pages/` 目录创建 `N_emoji_名称.py`
2. N 是页面顺序（从 1 开始）
3. 使用 `st.set_page_config()` 配置页面

### 添加新组件

1. 在 `components/` 目录创建组件文件
2. 导入必要的 Streamlit 模块
3. 在页面中导入使用

### API 调用

1. 使用 `frontend.utils.api_client.get_api_client()`
2. 所有 API 方法都是异步的，使用 `asyncio.run()` 调用
3. 处理异常情况
