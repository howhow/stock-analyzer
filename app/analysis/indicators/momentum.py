"""
动量指标

实现RSI、MACD动量指标
"""

import numpy as np
import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def rsi(
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    相对强弱指标 (Relative Strength Index)

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        RSI序列 (0-100)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 价格变化
    delta = close_prices.diff()

    # 上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    # 平均上涨和下跌
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # RS = 平均上涨 / 平均下跌
    rs = avg_gain / avg_loss

    # RSI = 100 - 100 / (1 + RS)
    rsi_series = 100 - (100 / (1 + rs))

    return rsi_series


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

    # 最高价和最低价
    highest_high = high_prices.rolling(window=k_period).max()
    lowest_low = low_prices.rolling(window=k_period).min()

    # K值 = (收盘价 - 最低价) / (最高价 - 最低价) * 100
    k_value = ((close_prices - lowest_low) / (highest_high - lowest_low)) * 100

    # D值 = K值的移动平均
    d_value = k_value.rolling(window=d_period).mean()

    return {
        "k": k_value,
        "d": d_value,
    }


def williams_r(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    威廉指标 (Williams %R)

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

    # 最高价和最低价
    highest_high = high_prices.rolling(window=period).max()
    lowest_low = low_prices.rolling(window=period).min()

    # Williams %R = (最高价 - 收盘价) / (最高价 - 最低价) * -100
    wr = ((highest_high - close_prices) / (highest_high - lowest_low)) * -100

    return wr


def momentum(
    close_prices: list[float] | pd.Series,
    period: int = 10,
) -> pd.Series:
    """
    动量指标 (Momentum)

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        动量序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 动量 = 当前价格 - N期前价格
    return close_prices - close_prices.shift(period)


def rate_of_change(
    close_prices: list[float] | pd.Series,
    period: int = 10,
) -> pd.Series:
    """
    变动率指标 (Rate of Change)

    Args:
        close_prices: 收盘价序列
        period: 周期

    Returns:
        ROC序列 (%)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # ROC = (当前价格 - N期前价格) / N期前价格 * 100
    roc = (
        (close_prices - close_prices.shift(period)) / close_prices.shift(period)
    ) * 100

    return roc


def cci(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    顺势指标 (Commodity Channel Index)

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

    # 典型价格 = (最高 + 最低 + 收盘) / 3
    tp = (high_prices + low_prices + close_prices) / 3

    # SMA
    sma = tp.rolling(window=period).mean()

    # 平均绝对偏差
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

    # CCI = (典型价格 - SMA) / (0.015 * MAD)
    cci_series = (tp - sma) / (0.015 * mad)

    return cci_series
