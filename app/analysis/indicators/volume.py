"""
成交量指标

使用 TA-Lib 实现成交量相关指标
"""

from typing import Any

import numpy as np
import pandas as pd
import talib

from app.utils.logger import get_logger

logger = get_logger(__name__)


def obv(
    close_prices: list[float] | pd.Series,
    volume: list[float] | pd.Series,
) -> pd.Series:
    """
    能量潮指标 (On Balance Volume)

    使用 TA-Lib OBV 实现

    Args:
        close_prices: 收盘价序列
        volume: 成交量序列

    Returns:
        OBV序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # TA-Lib OBV
    obv_values = talib.OBV(close_prices.values, volume.values)

    return pd.Series(obv_values, index=close_prices.index)


def ad(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volume: list[float] | pd.Series,
) -> pd.Series:
    """
    累积/派发线 (Accumulation/Distribution Line)

    使用 TA-Lib AD 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volume: 成交量序列

    Returns:
        AD序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # TA-Lib AD
    ad_values = talib.AD(
        high_prices.values, low_prices.values, close_prices.values, volume.values
    )

    return pd.Series(ad_values, index=close_prices.index)


def adosc(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volume: list[float] | pd.Series,
    fast_period: int = 3,
    slow_period: int = 10,
) -> pd.Series:
    """
    累积/派发震荡指标 (Accumulation/Distribution Oscillator)

    使用 TA-Lib ADOSC 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volume: 成交量序列
        fast_period: 快线周期
        slow_period: 慢线周期

    Returns:
        ADOSC序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # TA-Lib ADOSC
    adosc_values = talib.ADOSC(
        high_prices.values,
        low_prices.values,
        close_prices.values,
        volume.values,
        fastperiod=fast_period,
        slowperiod=slow_period,
    )

    return pd.Series(adosc_values, index=close_prices.index)


def mfi(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volume: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    资金流量指标 (Money Flow Index)

    使用 TA-Lib MFI 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volume: 成交量序列
        period: 周期

    Returns:
        MFI序列 (0-100)
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # TA-Lib MFI
    mfi_values = talib.MFI(
        high_prices.values,
        low_prices.values,
        close_prices.values,
        volume.values,
        timeperiod=period,
    )

    return pd.Series(mfi_values, index=close_prices.index)


def volume_rate(
    volume: list[float] | pd.Series,
    period: int = 5,
) -> pd.Series:
    """
    成交量比率

    Args:
        volume: 成交量序列
        period: 周期

    Returns:
        成交量比率序列
    """
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # 计算平均成交量
    avg_volume = volume.rolling(window=period).mean()

    # 成交量比率 = 当前成交量 / 平均成交量
    rate = volume / avg_volume

    return rate


def volume_ma(
    volume: list[float] | pd.Series,
    period: int = 5,
) -> pd.Series:
    """
    成交量移动平均

    Args:
        volume: 成交量序列
        period: 周期

    Returns:
        成交量移动平均序列
    """
    if isinstance(volume, list):
        volume = pd.Series(volume)

    return volume.rolling(window=period).mean()


def volume_spike(
    volume: list[float] | pd.Series,
    period: int = 20,
    threshold: float = 2.0,
) -> pd.Series:
    """
    成交量异常检测

    Args:
        volume: 成交量序列
        period: 周期
        threshold: 异常阈值（倍数）

    Returns:
        异常标志序列 (1: 放量, -1: 缩量, 0: 正常)
    """
    if isinstance(volume, list):
        volume = pd.Series(volume)

    # 计算平均成交量
    avg_volume = volume.rolling(window=period).mean()

    # 计算成交量比率
    rate = volume / avg_volume

    # 判断异常
    spike = pd.Series(0, index=volume.index)
    spike[rate >= threshold] = 1  # 放量
    spike[rate <= 1 / threshold] = -1  # 缩量

    return spike


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
