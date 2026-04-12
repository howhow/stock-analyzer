"""
动量指标

使用 TA-Lib 实现动量指标
"""

from typing import Any

import numpy as np
import pandas as pd
import talib

from app.utils.logger import get_logger

logger = get_logger(__name__)


def rsi(
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    相对强弱指标 (Relative Strength Index)

    使用 TA-Lib 实现，采用 Wilder's smoothing 算法

    Args:
        close_prices: 收盘价序列
        period: 周期（默认14）

    Returns:
        RSI序列 (0-100)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 边界检查
    if len(close_prices) == 0:
        return pd.Series([], dtype=float)

    # TA-Lib 需要 numpy array 且类型为 float64
    close_array = np.asarray(close_prices.values, dtype=np.float64)
    rsi_values = talib.RSI(close_array, timeperiod=period)

    return pd.Series(rsi_values, index=close_prices.index)


def rsi_signal(
    close_prices: list[float] | pd.Series,
    period: int = 14,
    overbought: float = 70,
    oversold: float = 30,
) -> pd.Series:
    """
    RSI交易信号

    Args:
        close_prices: 收盘价序列
        period: 周期
        overbought: 超买阈值
        oversold: 超卖阈值

    Returns:
        信号序列 (1: 买入, -1: 卖出, 0: 无信号)
    """
    rsi_series = rsi(close_prices, period)

    signal = pd.Series(0, index=rsi_series.index)

    # 超卖 → 买入信号
    signal[rsi_series < oversold] = 1

    # 超买 → 卖出信号
    signal[rsi_series > overbought] = -1

    return signal


def stochastic_oscillator(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> dict[str, pd.Series]:
    """
    随机指标 (Stochastic Oscillator)

    使用 TA-Lib STOCH 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        k_period: K值周期
        d_period: D值周期

    Returns:
        {'k': K值, 'd': D值}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib STOCH
    slowk, slowd = talib.STOCH(
        high_prices.values,
        low_prices.values,
        close_prices.values,
        fastk_period=k_period,
        slowk_period=d_period,
        slowk_matype=0,  # type: ignore[arg-type]
        slowd_period=d_period,
        slowd_matype=0,  # type: ignore[arg-type]
    )

    return {
        "k": pd.Series(slowk, index=close_prices.index),
        "d": pd.Series(slowd, index=close_prices.index),
    }


def williams_r(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    威廉指标 (Williams %R)

    使用 TA-Lib WILLR 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        Williams %R序列 (0到-100)
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib WILLR
    wr_values = talib.WILLR(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )

    return pd.Series(wr_values, index=close_prices.index)


def momentum(
    close_prices: list[float] | pd.Series,
    period: int = 10,
) -> pd.Series:
    """
    动量指标 (Momentum)

    使用 TA-Lib MOM 实现

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        动量序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib MOM
    mom_values = talib.MOM(close_prices.values, timeperiod=period)

    return pd.Series(mom_values, index=close_prices.index)


def rate_of_change(
    close_prices: list[float] | pd.Series,
    period: int = 10,
) -> pd.Series:
    """
    变动率指标 (Rate of Change)

    使用 TA-Lib ROC 实现

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        ROC序列 (%)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib ROC
    roc_values = talib.ROC(close_prices.values, timeperiod=period)

    return pd.Series(roc_values, index=close_prices.index)


def cci(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    顺势指标 (Commodity Channel Index)

    使用 TA-Lib CCI 实现

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        period: 周期

    Returns:
        CCI序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # TA-Lib CCI
    cci_values = talib.CCI(
        high_prices.values, low_prices.values, close_prices.values, timeperiod=period
    )

    return pd.Series(cci_values, index=close_prices.index)


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
