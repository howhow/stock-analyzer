"""
波动率指标

实现ATR等波动率指标
"""

import numpy as np
import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def atr(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    平均真实波幅 (Average True Range)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        ATR序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 计算真实波幅
    prev_close = close_prices.shift(1)

    tr1 = high_prices - low_prices  # 当日最高-最低
    tr2 = abs(high_prices - prev_close)  # 当日最高-前收
    tr3 = abs(low_prices - prev_close)  # 当日最低-前收

    # 真实波幅取三者最大
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR = 真实波幅的移动平均
    atr_series = tr.rolling(window=period).mean()

    return atr_series


def atr_percentage(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    ATR百分比 (ATR / 收盘价)

    用于衡量相对波动率

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        ATR百分比序列
    """
    atr_series = atr(high_prices, low_prices, close_prices, period)

    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    return (atr_series / close_prices) * 100


def volatility(
    close_prices: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    历史波动率 (标准差)

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        波动率序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 收益率
    returns = close_prices.pct_change()

    # 波动率 = 收益率的标准差
    volatility_series = returns.rolling(window=period).std() * np.sqrt(252)

    return volatility_series


def keltner_channels(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 20,
    atr_multiplier: float = 2.0,
) -> dict[str, pd.Series]:
    """
    肯特纳通道 (Keltner Channels)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期
        atr_multiplier: ATR倍数

    Returns:
        {'upper': 上轨, 'middle': 中轨, 'lower': 下轨}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 中轨 = EMA
    from app.analysis.indicators.trend import ema

    middle = ema(close_prices, period)

    # ATR
    atr_series = atr(high_prices, low_prices, close_prices, period)

    # 上下轨
    upper = middle + atr_multiplier * atr_series
    lower = middle - atr_multiplier * atr_series

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
    }


def volatility_regime(
    close_prices: list[float] | pd.Series,
    short_period: int = 10,
    long_period: int = 60,
) -> pd.Series:
    """
    波动率状态判断

    判断当前是高波动还是低波动状态

    Args:
        close_prices: 收盘价序列
        short_period: 短期周期
        long_period: 长期周期

    Returns:
        状态序列 (1: 高波动, -1: 低波动, 0: 正常)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 短期和长期波动率
    short_vol = volatility(close_prices, short_period)
    long_vol = volatility(close_prices, long_period)

    # 波动率比率
    vol_ratio = short_vol / long_vol

    # 状态判断
    regime = pd.Series(0, index=close_prices.index)
    regime[vol_ratio > 1.5] = 1  # 高波动
    regime[vol_ratio < 0.7] = -1  # 低波动

    return regime
