# AlgorithmCore 使用指南

## 概述

`AlgorithmCore` 是 Stock Analyzer 项目的算法核心模块，负责：
1. **指标计算**：调用 TA-Lib 或自定义指标
2. **AI辅助**：调用 AI 提供商进行分析
3. **算法编排**：组合多个算法生成结果

## 核心功能

### 1. 指标管理

#### 注册自定义指标

```python
from framework.core.algorithm_core import AlgorithmCore
from framework.interfaces.indicator import IndicatorInterface
import pandas as pd

class CustomRSI:
    @property
    def name(self) -> str:
        return "custom_rsi"
    
    @property
    def params(self) -> dict:
        return {
            "period": {
                "type": "int",
                "default": 14,
                "description": "RSI period"
            }
        }
    
    @property
    def description(self) -> str:
        return "Custom RSI indicator"
    
    @property
    def required_columns(self) -> list[str]:
        return ["close"]
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        period = kwargs.get("period", 14)
        # 自定义计算逻辑
        return custom_rsi_logic(data["close"], period)
    
    def validate_params(self, **kwargs) -> bool:
        period = kwargs.get("period", 14)
        return period > 0

# 注册指标
core = AlgorithmCore()
core.register_indicator(CustomRSI())
```

#### 计算单个指标

```python
import pandas as pd

# 准备数据
df = pd.DataFrame({
    'close': [100, 101, 102, 103, 104, 105]
})

# 计算指标
rsi_result = await core.calculate_indicator('rsi', df, period=14)
sma_result = await core.calculate_indicator('sma', df, period=20)
```

#### 批量计算指标

```python
# 批量计算多个指标
results = await core.calculate_indicators(
    df,
    indicator_names=['rsi', 'macd', 'sma'],
    params={
        'rsi': {'period': 14},
        'sma': {'period': 20},
        'macd': {'fast_period': 12, 'slow_period': 26}
    }
)

# 访问结果
rsi = results['rsi']
macd = results['macd']
```

### 2. 内置指标

AlgorithmCore 内置了以下 TA-Lib 指标：

#### 趋势指标
- `sma` - 简单移动平均线
- `ema` - 指数移动平均线
- `macd` - MACD 指标
- `bollinger_bands` - 布林通道

#### 动量指标
- `rsi` - 相对强弱指标
- `momentum` - 动量指标
- `rate_of_change` - 变化率
- `stochastic_oscillator` - 随机指标
- `williams_r` - 威廉指标

#### 波动率指标
- `atr` - 平均真实波幅

#### 成交量指标
- `obv` - 能量潮
- `money_flow_index` - 资金流量指标

#### 指标所需列

| 指标 | 所需列 |
|------|--------|
| sma, ema, rsi, momentum, rate_of_change | close |
| macd, bollinger_bands | close |
| atr, stochastic_oscillator, williams_r | high, low, close |
| obv | close, volume |
| money_flow_index | high, low, close, volume |

### 3. AI 辅助分析

#### 注册 AI 提供商

```python
from framework.interfaces.ai_provider import AIProviderInterface

class OpenAIProvider:
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def supported_models(self) -> list[str]:
        return ["gpt-4", "gpt-3.5-turbo"]
    
    async def analyze(
        self,
        data: dict[str, Any],
        task: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        # 实现 AI 分析逻辑
        return {"analysis": "...", "confidence": 0.85}
    
    async def health_check(self) -> bool:
        return True

# 注册提供商
core.register_ai_provider(OpenAIProvider())
```

#### 使用 AI 分析

```python
# 准备分析数据
analysis_data = {
    "rsi": 70,
    "macd": {"macd": 0.5, "signal": 0.3},
    "trend": "upward"
}

# 执行分析
result = await core.analyze_with_ai(
    data=analysis_data,
    task="分析当前市场状态并给出交易建议",
    provider="openai",  # 可选，默认使用第一个注册的提供商
    model="gpt-4"       # 可选
)

print(result)
# {
#     "task": "分析当前市场状态并给出交易建议",
#     "data": {...},
#     "result": "市场处于超买状态...",
#     "confidence": 0.85
# }
```

### 4. 异常处理

```python
from framework.core.algorithm_core import (
    IndicatorNotFoundError,
    IndicatorCalculationError,
    AIProviderNotFoundError,
    AIAnalysisError,
)

try:
    result = await core.calculate_indicator('nonexistent', df)
except IndicatorNotFoundError as e:
    print(f"指标未找到: {e.name}")

try:
    result = await core.calculate_indicator('rsi', df_missing_columns)
except IndicatorCalculationError as e:
    print(f"计算失败 '{e.name}': {e.reason}")

try:
    result = await core.analyze_with_ai(data, "分析任务")
except AIProviderNotFoundError as e:
    print(f"AI提供商未找到: {e.name}")
except AIAnalysisError as e:
    print(f"AI分析失败: {e.reason}")
```

### 5. 健康检查

```python
# 执行健康检查
status = await core.health_check()

print(status)
# {
#     "status": "healthy",  # 或 "degraded"
#     "indicators": {
#         "custom": 2,
#         "builtin": 12
#     },
#     "ai_providers": {
#         "openai": {
#             "status": "healthy",
#             "models": ["gpt-4", "gpt-3.5-turbo"]
#         }
#     }
# }
```

## 完整示例

```python
import asyncio
import pandas as pd
from framework.core.algorithm_core import AlgorithmCore

async def main():
    # 1. 初始化
    core = AlgorithmCore()
    
    # 2. 准备数据
    df = pd.DataFrame({
        'high': [105, 106, 107, 108, 109, 110],
        'low': [95, 96, 97, 98, 99, 100],
        'close': [100, 101, 102, 103, 104, 105],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500]
    })
    
    # 3. 批量计算指标
    indicators = await core.calculate_indicators(
        df,
        ['rsi', 'sma', 'macd', 'atr'],
        {'rsi': {'period': 14}, 'sma': {'period': 5}}
    )
    
    # 4. AI 分析
    analysis_data = {
        "rsi": indicators['rsi'].iloc[-1],
        "atr": indicators['atr'].iloc[-1],
        "close": df['close'].iloc[-1]
    }
    
    result = await core.analyze_with_ai(
        analysis_data,
        "基于指标数据给出交易建议"
    )
    
    print("指标计算结果:", indicators.keys())
    print("AI分析结果:", result)
    
    # 5. 健康检查
    status = await core.health_check()
    print("系统状态:", status['status'])

asyncio.run(main())
```

## 最佳实践

### 1. 异步并发

AlgorithmCore 的所有计算方法都是异步的，可以并发执行：

```python
# 并发计算多个不相关的指标
import asyncio

tasks = [
    core.calculate_indicator('rsi', df, period=14),
    core.calculate_indicator('macd', df),
    core.calculate_indicator('atr', df),
]

results = await asyncio.gather(*tasks)
```

### 2. 错误处理

建议在生产环境中使用完善的错误处理：

```python
from framework.core.algorithm_core import (
    IndicatorNotFoundError,
    IndicatorCalculationError,
)

async def safe_calculate(core, name, df, **kwargs):
    try:
        return await core.calculate_indicator(name, df, **kwargs)
    except IndicatorNotFoundError:
        logger.warning(f"Indicator {name} not found, skipping")
        return None
    except IndicatorCalculationError as e:
        logger.error(f"Calculation failed: {e.reason}")
        raise
```

### 3. 数据验证

在计算前验证数据完整性：

```python
def validate_ohlc_data(df: pd.DataFrame) -> bool:
    required = ['open', 'high', 'low', 'close', 'volume']
    return all(col in df.columns for col in required)

if not validate_ohlc_data(df):
    raise ValueError("Missing required OHLCV columns")
```

## 性能优化

### 1. 批量计算

使用 `calculate_indicators` 批量计算比单个计算更高效：

```python
# ✓ 推荐：批量计算
results = await core.calculate_indicators(df, ['rsi', 'macd', 'sma'])

# ✗ 不推荐：循环单个计算
results = {}
for name in ['rsi', 'macd', 'sma']:
    results[name] = await core.calculate_indicator(name, df)
```

### 2. 缓存结果

对于不经常变化的数据，建议缓存计算结果：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_indicator(symbol: str, indicator: str, params: tuple):
    df = await fetch_data(symbol)
    return await core.calculate_indicator(indicator, df, **dict(params))
```

## 总结

AlgorithmCore 提供了一个统一的接口来：
- 管理和计算技术指标（自定义 + 内置）
- 集成多个 AI 提供商进行分析
- 执行系统健康检查
- 处理各种异常情况

通过异步 API 和批量计算支持，确保了高性能和可扩展性。
