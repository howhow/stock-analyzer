"""
技术指标模块

提供常用技术指标计算（使用 TA-Lib 实现）
"""

from app.analysis.indicators.momentum import (
    cci,
    macd,  # 添加 MACD 到 momentum（已实现）
    momentum,
    rate_of_change,
    rsi,
    rsi_signal,
    stochastic_oscillator,
    williams_r,
)
from app.analysis.indicators.trend import (
    bollinger_bands,
    ema,
    golden_cross,
    sma,
    support_resistance,
    trend_direction,
)
from app.analysis.indicators.volatility import (
    atr,
    bollinger_bands as bollinger_bands_volatility,  # 别名
    donchian_channel,
    historical_volatility,
    keltner_channel,
)
from app.analysis.indicators.volume import (
    ad as accumulation_distribution,  # 别名
    adosc,
    mfi as money_flow_index,  # 别名
    obv,
    vwap,
    volume_ma,
    volume_rate as volume_ratio,  # 别名
    volume_spike,
)


# 定义别名函数（向后兼容）
def atr_percentage(high_prices, low_prices, close_prices, period: int = 14):
    """ATR占价格百分比"""
    from app.analysis.indicators.volatility import atr

    atr_values = atr(high_prices, low_prices, close_prices, period)
    if hasattr(close_prices, "iloc"):
        close = close_prices.iloc[-1] if len(close_prices) > 0 else 1
    else:
        close = close_prices[-1] if len(close_prices) > 0 else 1
    return (atr_values / close) * 100


def volatility(close_prices, period: int = 20):
    """历史波动率（别名）"""
    from app.analysis.indicators.volatility import historical_volatility

    return historical_volatility(close_prices, period)


def keltner_channels(
    high_prices, low_prices, close_prices, period: int = 20, atr_multiplier: float = 2.0
):
    """肯特纳通道（别名）"""
    from app.analysis.indicators.volatility import keltner_channel

    return keltner_channel(
        high_prices, low_prices, close_prices, period, atr_multiplier
    )


def volatility_regime(close_prices, period: int = 20):
    """波动率状态判断"""
    from app.analysis.indicators.volatility import historical_volatility
    import pandas as pd
    import numpy as np

    hv = historical_volatility(close_prices, period)

    if len(hv) == 0 or pd.isna(hv.iloc[-1]):
        return "unknown"

    # 简单的状态判断
    avg_hv = hv.rolling(window=period).mean()
    current_hv = hv.iloc[-1]
    avg_value = (
        avg_hv.iloc[-1]
        if len(avg_hv) > 0 and not pd.isna(avg_hv.iloc[-1])
        else current_hv
    )

    if current_hv > avg_value * 1.5:
        return "high"
    elif current_hv < avg_value * 0.5:
        return "low"
    else:
        return "normal"


def chaikin_money_flow(high_prices, low_prices, close_prices, volume, period: int = 20):
    """佳庆资金流量指标"""
    from app.analysis.indicators.volume import ad
    import pandas as pd

    ad_values = ad(high_prices, low_prices, close_prices, volume)

    if isinstance(volume, list):
        volume = pd.Series(volume)

    # CMF = SUM(AD, period) / SUM(Volume, period)
    cmf = ad_values.rolling(window=period).sum() / volume.rolling(window=period).sum()

    return cmf


def volume_price_trend(close_prices, volume):
    """成交量价格趋势"""
    import pandas as pd

    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # VPT = VPT_prev + Volume * (Close - Close_prev) / Close_prev
    price_change = close_prices.pct_change()
    vpt = (volume * price_change).cumsum()

    return vpt


__all__ = [
    # 趋势指标
    "sma",
    "ema",
    "macd",
    "bollinger_bands",
    "trend_direction",
    "golden_cross",
    "support_resistance",
    # 波动率指标
    "atr",
    "atr_percentage",
    "volatility",
    "keltner_channels",
    "volatility_regime",
    # 动量指标
    "rsi",
    "rsi_signal",
    "stochastic_oscillator",
    "williams_r",
    "momentum",
    "rate_of_change",
    "cci",
    # 成交量指标
    "obv",
    "volume_ma",
    "volume_ratio",
    "money_flow_index",
    "accumulation_distribution",
    "chaikin_money_flow",
    "volume_price_trend",
]
