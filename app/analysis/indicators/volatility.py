"""
波动率指标

使用 TA-Lib 实现波动率指标
"""

from typing import Any

import numpy as np
import pandas as pd
import talib

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

    使用 TA-Lib ATR 实现

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

    # TA-Lib ATR
    atr_values = talib.ATR(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )

    return pd.Series(atr_values, index=close_prices.index)


def adx(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> dict[str, pd.Series]:
    """
    平均趋向指标 (Average Directional Index)

    使用 TA-Lib ADX 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        {'adx': ADX值, 'plus_di': +DI, 'minus_di': -DI}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib ADX, PLUS_DI, MINUS_DI
    adx_values = talib.ADX(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )
    plus_di = talib.PLUS_DI(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )
    minus_di = talib.MINUS_DI(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )

    return {
        "adx": pd.Series(adx_values, index=close_prices.index),
        "plus_di": pd.Series(plus_di, index=close_prices.index),
        "minus_di": pd.Series(minus_di, index=close_prices.index),
    }


def bollinger_bands(
    close_prices: list[float] | pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, pd.Series]:
    """
    布林通道 (Bollinger Bands)

    使用 TA-Lib BBANDS 实现

    Args:
        close_prices: 收盘价序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        {'upper': 上轨, 'middle': 中轨, 'lower': 下轨, 'width': 带宽}
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib BBANDS
    upper, middle, lower = talib.BBANDS(
        close_prices.values,
        timeperiod=period,
        nbdevup=std_dev,
        nbdevdn=std_dev,
        matype=0,
    )

    # 计算带宽
    width = (upper - lower) / middle

    return {
        "upper": pd.Series(upper, index=close_prices.index),
        "middle": pd.Series(middle, index=close_prices.index),
        "lower": pd.Series(lower, index=close_prices.index),
        "width": pd.Series(width, index=close_prices.index),
    }


def historical_volatility(
    close_prices: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    历史波动率 (Historical Volatility)

    计算收益率的标准差（年化）

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        历史波动率序列（年化）
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 计算日收益率
    returns = close_prices.pct_change()

    # 计算滚动标准差
    volatility = returns.rolling(window=period).std()

    # 年化（假设252个交易日）
    annualized_volatility = volatility * np.sqrt(252)

    return annualized_volatility


def keltner_channel(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 20,
    atr_multiplier: float = 2.0,
) -> dict[str, pd.Series]:
    """
    肯特纳通道 (Keltner Channel)

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

    # 计算EMA和ATR
    middle = talib.EMA(close_prices.values, timeperiod=period)
    atr_values = talib.ATR(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )

    # 计算上下轨
    upper = middle + (atr_values * atr_multiplier)
    lower = middle - (atr_values * atr_multiplier)

    return {
        "upper": pd.Series(upper, index=close_prices.index),
        "middle": pd.Series(middle, index=close_prices.index),
        "lower": pd.Series(lower, index=close_prices.index),
    }


def donchian_channel(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    period: int = 20,
) -> dict[str, pd.Series]:
    """
    唐奇安通道 (Donchian Channel)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        period: 周期

    Returns:
        {'upper': 上轨, 'middle': 中轨, 'lower': 下轨}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)

    # 上轨：period期间最高价的最大值
    upper = high_prices.rolling(window=period).max()

    # 下轨：period期间最低价的最小值
    lower = low_prices.rolling(window=period).min()

    # 中轨：上下轨的平均值
    middle = (upper + lower) / 2

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
    }
