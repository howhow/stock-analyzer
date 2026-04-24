# OpenBB 数据源插件

## 概述

OpenBB 插件是 **可选数据源**，提供全球市场行情数据支持。

## 安装

OpenBB 不是核心依赖，需要单独安装：

```bash
pip install openbb
```

## 支持的市场

| 市场 | 代码后缀 | 说明 |
|------|----------|------|
| A股 - 上海 | .SS | 上证 |
| A股 - 深圳 | .SZ | 深证 |
| 港股 | .HK | 香港 |
| 美股 | 无后缀 | 如 AAPL, TSLA |

## DataHub 集成

OpenBB 插件支持 DataHub 标准接口：

```python
from framework.data.hub import DataHub
from plugins.data_sources.openbb.plugin import OpenBBPlugin

# 创建插件
openbb = OpenBBPlugin()

# 使用 DataHub
datahub = DataHub(sources=[openbb])

# 获取数据
df = await datahub.fetch_daily("AAPL")
```

## 优先级

OpenBB 插件优先级为 **30**（数值越大优先级越低），作为 Tushare/AKShare 的备用数据源。

## 注意事项

1. **A股数据有限** - OpenBB 对 A 股支持不如 Tushare 完善
2. **全球数据优势** - 美股、港股数据更完整
3. **网络依赖** - 需要访问 OpenBB 服务器

## 故障排除

### OpenBB SDK 未安装

```
OpenBBClientError: OpenBB SDK 未安装
```

**解决**: `pip install openbb`

### 股票代码格式

OpenBB 使用特殊代码格式：
- 贵州茅台: `600519.SS`（不是 `600519.SH`）
- 腾讯: `0700.HK`
- 苹果: `AAPL`

插件会自动转换标准格式到 OpenBB 格式。
