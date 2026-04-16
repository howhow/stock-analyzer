# Tushare 数据源插件

A 股专业数据源插件，提供深度财务数据、机构持仓等。

## 特性

- ✓ 实现 `DataSourceInterface` 接口
- ✓ 异步 API 调用（使用 asyncio）
- ✓ 熔断器保护
- ✓ 自动重试机制
- ✓ 速率限制处理
- ✓ 数据质量评估
- ✓ 完整的类型注解
- ✓ 详细的日志记录

## 支持市场

- SH - 上海证券交易所
- SZ - 深圳证券交易所

## 安装

```bash
pip install tushare>=1.2.0
```

## 配置

在 `.env` 文件中配置 Tushare Token：

```env
TUSHARE_TOKEN=your_token_here
```

或通过环境变量：

```bash
export TUSHARE_TOKEN=your_token_here
```

## 使用示例

### 基本使用

```python
from datetime import date
from plugins.data_sources.tushare import TusharePlugin

# 创建插件实例
plugin = TusharePlugin()

# 获取日线行情
quotes = await plugin.get_quotes(
    stock_code="600519.SH",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
)

for quote in quotes:
    print(f"{quote.trade_date}: {quote.close}")

# 健康检查
is_healthy = await plugin.health_check()
print(f"数据源健康: {is_healthy}")

# 获取支持的股票列表
stocks = await plugin.get_supported_stocks("SH")
print(f"上交所股票数量: {len(stocks)}")
```

### 自定义配置

```python
from plugins.data_sources.tushare import TusharePlugin

# 自定义超时和重试次数
plugin = TusharePlugin(
    token="your_token",
    timeout=30,  # 30秒超时
    max_retries=5,  # 最多重试5次
)
```

## 模块结构

```
plugins/data_sources/tushare/
├── __init__.py        # 包初始化，导出 TusharePlugin
├── plugin.py          # 插件主文件，实现 DataSourceInterface
├── client.py          # Tushare API 客户端
├── mapper.py          # 数据转换器
├── exceptions.py      # 自定义异常
└── README.md          # 本文档
```

## API 文档

### TusharePlugin

#### 属性

- `name: str` - 数据源名称（"tushare"）
- `supported_markets: list[str]` - 支持的市场列表（["SH", "SZ"]）

#### 方法

##### `get_quotes(stock_code: str, start_date: date, end_date: date) -> list[StandardQuote]`

获取历史行情数据。

**参数：**
- `stock_code` - 股票代码（如 '600519.SH'）
- `start_date` - 开始日期
- `end_date` - 结束日期

**返回：**
- StandardQuote 列表，包含日线行情数据

**异常：**
- `TushareAuthError` - Token 无效
- `TushareNoDataError` - 无数据
- `TushareRateLimitError` - 速率限制
- `TushareTimeoutError` - 请求超时

##### `get_realtime_quote(stock_code: str) -> StandardQuote | None`

获取实时行情。

**注意：** Tushare 免费版不支持实时行情，需要 Pro 权限。

**参数：**
- `stock_code` - 股票代码

**返回：**
- StandardQuote 实例，如果不支持则返回 None

##### `health_check() -> bool`

健康检查，验证 Token 是否有效。

**返回：**
- True 如果数据源可用，False 否则

##### `get_supported_stocks(market: str) -> list[str]`

获取市场支持的股票列表。

**参数：**
- `market` - 市场代码（SH 或 SZ）

**返回：**
- 股票代码列表

## 数据质量

插件会自动计算以下质量指标：

### 完整度评分（completeness）

基于字段存在情况计算（0-1）：
- 价格字段（60%）：open, high, low, close
- 成交字段（40%）：volume, amount

### 质量评分（quality_score）

基于数据合理性计算（0-1）：
- 价格逻辑正确性（最高 >= 最低，收盘价在范围内）
- 价格有效性（正数、非零）

## 异常处理

```python
from plugins.data_sources.tushare.exceptions import (
    TushareError,           # 基础异常
    TushareAuthError,       # 认证错误
    TushareRateLimitError,  # 速率限制
    TushareTimeoutError,    # 请求超时
    TushareNoDataError,     # 无数据
    TushareCircuitBreakerError,  # 熔断器开启
)

try:
    quotes = await plugin.get_quotes("600519.SH", start_date, end_date)
except TushareAuthError:
    print("Token 无效，请检查配置")
except TushareRateLimitError as e:
    print(f"速率限制，请 {e.retry_after} 秒后重试")
except TushareNoDataError:
    print("未找到数据")
```

## 注意事项

1. **Token 配置** - 必须配置有效的 Tushare Token 才能使用
2. **速率限制** - 免费版有调用频率限制，插件会自动处理
3. **实时行情** - 免费版不支持实时行情，需要 Pro 权限
4. **错误处理** - 所有 API 调用都有异常处理和重试机制

## 依赖

- Python 3.11+
- tushare >= 1.2.0
- pandas
- pydantic

## 许可证

MIT License
