# AKShare 数据源插件

提供 A 股行情数据获取功能，基于 AKShare 开源财经数据接口。

## 特性

- ✅ 实现 `DataSourceInterface` 接口协议
- ✅ 支持上交所（SH）和深交所（SZ）
- ✅ 历史行情数据获取（日线）
- ✅ 实时行情数据获取
- ✅ 健康检查
- ✅ 股票列表获取
- ✅ 自动重试机制
- ✅ 数据质量评分

## 安装

```bash
pip install akshare
```

## 使用示例

### 1. 基本使用

```python
from datetime import date
from plugins.data_sources.akshare import AKSharePlugin

# 创建插件实例
plugin = AKSharePlugin()

# 获取历史行情
quotes = await plugin.get_quotes(
    stock_code="600519.SH",  # 贵州茅台
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
)

for quote in quotes:
    print(f"{quote.trade_date}: {quote.close}")
```

### 2. 获取实时行情

```python
# 获取实时行情
quote = await plugin.get_realtime_quote("000001.SZ")

if quote:
    print(f"最新价: {quote.close}")
    print(f"开盘价: {quote.open}")
    print(f"最高价: {quote.high}")
    print(f"最低价: {quote.low}")
```

### 3. 健康检查

```python
# 检查数据源是否可用
is_healthy = await plugin.health_check()

if is_healthy:
    print("AKShare 服务可用")
else:
    print("AKShare 服务不可用")
```

### 4. 获取股票列表

```python
# 获取上交所股票列表
stocks = await plugin.get_supported_stocks("SH")

print(f"上交所股票数量: {len(stocks)}")
print(f"前 10 只: {stocks[:10]}")
```

## 数据模型

返回的 `StandardQuote` 对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码 |
| trade_date | date | 交易日期 |
| open | float \| None | 开盘价 |
| high | float \| None | 最高价 |
| low | float \| None | 最低价 |
| close | float | 收盘价（必填） |
| volume | int \| None | 成交量 |
| amount | float \| None | 成交额 |
| turnover_rate | float \| None | 换手率 |
| source | str | 数据源名称 |
| completeness | float | 数据完整度（0-1） |
| quality_score | float | 数据质量评分（0-1） |

## 文件结构

```
plugins/data_sources/akshare/
├── __init__.py       # 插件入口
├── plugin.py         # 插件实现（DataSourceInterface）
├── client.py         # AKShare API 客户端
└── mapper.py         # 数据转换器
```

## 错误处理

插件内置重试机制，最多重试 3 次：

```python
# 自定义重试次数
plugin = AKSharePlugin(
    timeout=15,      # 超时时间（秒）
    max_retries=5,   # 最大重试次数
)
```

## 注意事项

1. **市场支持**：目前仅支持上交所（SH）和深交所（SZ）
2. **实时数据**：实时行情可能在非交易时间无法获取
3. **网络依赖**：需要稳定的网络连接
4. **免费数据**：AKShare 是免费数据源，无需 token

## 测试

运行测试脚本验证插件功能：

```bash
python test_akshare_plugin.py
```

测试内容：
- ✅ 导入检查
- ✅ 接口协议检查
- ✅ 健康检查
- ✅ 历史行情获取
- ✅ 实时行情获取
- ✅ 股票列表获取

## 版本

- 版本：1.0.0
- 创建日期：2026-04-16
- 作者：Agent-BackendDev
