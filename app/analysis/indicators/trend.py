"""
趋势指标

使用 TA-Lib 实现移动平均线等趋势指标
"""

from typing import Any

import numpy as np
import pandas as pd
import talib

from app.utils.logger import get_logger

logger = get_logger(__name__)


def sma(data: list[float] | pd.Series, period: int) -> pd.Series:
    """
    简单移动平均线 (Simple Moving Average)

    使用 TA-Lib MA 实现

    Args:
        data: 价格数据序列
        period: 周期

    Returns:
        SMA序列
    """
    if isinstance(data, list):
        data = pd.Series(data)

    # 边界检查
    if len(data) == 0:
        return pd.Series([], dtype=float)

    # TA-Lib 需要 numpy array 且类型为 float64
    data_array = np.asarray(data.values, dtype=np.float64)
    # mypy 无法识别 TA-Lib 的 MA_Type 枚举
    ma_values = talib.MA(data_array, timeperiod=period, matype=0)  # type: ignore

    return pd.Series(ma_values, index=data.index)


def ema(data: list[float] | pd.Series, period: int) -> pd.Series:
    """
    指数移动平均线 (Exponential Moving Average)

    使用 TA-Lib EMA 实现

    Args:
        data: 价格数据序列
        period: 周期

    Returns:
        EMA序列
    """
    if isinstance(data, list):
        data = pd.Series(data)

    # TA-Lib EMA
    ema_values = talib.EMA(data.values, timeperiod=period)

    return pd.Series(ema_values, index=data.index)


def macd(
    close_prices: list[float] | pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict[str, pd.Series]:
    """
    MACD指标 (Moving Average Convergence Divergence)

    使用 TA-Lib MACD 实现

    Args:
        close_prices: 收盘价序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期

    Returns:
        {'macd': MACD线, 'signal': 信号线, 'histogram': 柱状图}
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib MACD
    macd_line, signal_line, histogram = talib.MACD(
        close_prices.values,
        fastperiod=fast_period,
        slowperiod=slow_period,
        signalperiod=signal_period,
    )

    return {
        "macd": pd.Series(macd_line, index=close_prices.index),
        "signal": pd.Series(signal_line, index=close_prices.index),
        "histogram": pd.Series(histogram, index=close_prices.index),
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
        {'upper': 上轨, 'middle': 中轨, 'lower': 下轨}
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib BBANDS
    upper, middle, lower = talib.BBANDS(
        close_prices.values,
        timeperiod=period,
        nbdevup=std_dev,
        nbdevdn=std_dev,
        matype=0,  # type: ignore[arg-type]
    )

    return {
        "upper": pd.Series(upper, index=close_prices.index),
        "middle": pd.Series(middle, index=close_prices.index),
        "lower": pd.Series(lower, index=close_prices.index),
    }


def trend_direction(
    close_prices: list[float] | pd.Series,
    short_period: int = 5,
    long_period: int = 20,
) -> pd.Series:
    """
    趋势方向判断

    Args:
        close_prices: 收盘价序列
        short_period: 短期均线周期
        long_period: 长期均线周期

    Returns:
        趋势方向 (1: 上升趋势, -1: 下降趋势, 0: 震荡)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    short_ma = sma(close_prices, short_period)
    long_ma = sma(close_prices, long_period)

    trend = pd.Series(0, index=close_prices.index)

    # 金叉 → 上升趋势
    trend[short_ma > long_ma] = 1

    # 死叉 → 下降趋势
    trend[short_ma < long_ma] = -1

    return trend


def golden_cross(
    close_prices: list[float] | pd.Series,
    short_period: int = 5,
    long_period: int = 20,
) -> pd.Series:
    """
    金叉/死叉信号

    Args:
        close_prices: 收盘价序列
        short_period: 短期均线周期
        long_period: 长期均线周期

    Returns:
        信号序列 (1: 金叉, -1: 死叉, 0: 无信号)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    short_ma = sma(close_prices, short_period)
    long_ma = sma(close_prices, long_period)

    # 计算差值
    diff = short_ma - long_ma

    # 金叉：短期从下往上穿越长期
    golden = (diff > 0) & (diff.shift(1) <= 0)

    # 死叉：短期从上往下穿越长期
    death = (diff < 0) & (diff.shift(1) >= 0)

    signal = pd.Series(0, index=close_prices.index)
    signal[golden] = 1
    signal[death] = -1

    return signal


def support_resistance(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 20,
) -> dict[str, float]:
    """
    支撑位和阻力位

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        {'support': 支撑位, 'resistance': 阻力位, 'current_position': 当前价格位置(0-1)}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 使用最近 period 天的最高价作为阻力位
    resistance = float(high_prices.tail(period).max())

    # 使用最近 period 天的最低价作为支撑位
    support = float(low_prices.tail(period).min())

    # 计算当前价格在支撑阻力位之间的位置 (0-1)
    current_price = float(close_prices.iloc[-1])
    if resistance != support:
        current_position = (current_price - support) / (resistance - support)
        # 限制在 0-1 范围内
        current_position = max(0.0, min(1.0, current_position))
    else:
        current_position = 0.5

    return {
        "support": support,
        "resistance": resistance,
        "current_position": current_position,
    }


def vwap(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volume: list[float] | pd.Series,
) -> pd.Series:
    """
    成交量加权平均价格 (Volume Weighted Average Price)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volume: 成交量序列

    Returns:
        VWAP序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # 典型价格
    typical_price = (high_prices + low_prices + close_prices) / 3

    # VWAP = 累计(典型价格 * 成交量) / 累计成交量
    cum_tp_volume = (typical_price * volume).cumsum()
    cum_volume = volume.cumsum()

    vwap_values = cum_tp_volume / cum_volume

    return vwap_values
