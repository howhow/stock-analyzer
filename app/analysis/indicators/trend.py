"""
趋势指标

实现移动平均线等趋势指标
"""


import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def sma(data: list[float] | pd.Series, period: int) -> pd.Series:
    """
    简单移动平均线 (Simple Moving Average)

    Args:
        data: 价格数据序列
        period: 周期

    Returns:
        SMA序列
    """
    if isinstance(data, list):
        data = pd.Series(data)

    return data.rolling(window=period).mean()


def ema(data: list[float] | pd.Series, period: int) -> pd.Series:
    """
    指数移动平均线 (Exponential Moving Average)

    Args:
        data: 价格数据序列
        period: 周期

    Returns:
        EMA序列
    """
    if isinstance(data, list):
        data = pd.Series(data)

    return data.ewm(span=period, adjust=False).mean()


def macd(
    close_prices: list[float] | pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict[str, pd.Series]:
    """
    MACD指标 (Moving Average Convergence Divergence)

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

    # 快慢EMA
    ema_fast = ema(close_prices, fast_period)
    ema_slow = ema(close_prices, slow_period)

    # MACD线 = 快线 - 慢线
    macd_line = ema_fast - ema_slow

    # 信号线 = MACD的EMA
    signal_line = ema(macd_line, signal_period)

    # 柱状图 = MACD - 信号线
    histogram = macd_line - signal_line

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def bollinger_bands(
    close_prices: list[float] | pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, pd.Series]:
    """
    布林带 (Bollinger Bands)

    Args:
        close_prices: 收盘价序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        {'upper': 上轨, 'middle': 中轨, 'lower': 下轨}
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 中轨 = SMA
    middle = sma(close_prices, period)

    # 标准差
    std = close_prices.rolling(window=period).std()

    # 上下轨
    upper = middle + std_dev * std
    lower = middle - std_dev * std

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
    }


def trend_direction(
    close_prices: list[float] | pd.Series,
    short_period: int = 5,
    long_period: int = 20,
) -> pd.Series:
    """
    趋势方向判断

    基于短期和长期均线的关系判断趋势

    Args:
        close_prices: 收盘价序列
        short_period: 短期周期
        long_period: 长期周期

    Returns:
        趋势方向序列 (1: 上涨, -1: 下跌, 0: 震荡)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    short_ma = ema(close_prices, short_period)
    long_ma = ema(close_prices, long_period)

    # 趋势判断
    trend = pd.Series(0, index=close_prices.index)
    trend[short_ma > long_ma] = 1  # 上涨趋势
    trend[short_ma < long_ma] = -1  # 下跌趋势

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
        short_period: 短期周期
        long_period: 长期周期

    Returns:
        信号序列 (1: 金叉, -1: 死叉, 0: 无信号)
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    short_ma = ema(close_prices, short_period)
    long_ma = ema(close_prices, long_period)

    # 计算差值
    diff = short_ma - long_ma
    prev_diff = diff.shift(1)

    # 信号判断
    signal = pd.Series(0, index=close_prices.index)

    # 金叉：短期从下向上穿越长期
    signal[(prev_diff <= 0) & (diff > 0)] = 1

    # 死叉：短期从上向下穿越长期
    signal[(prev_diff >= 0) & (diff < 0)] = -1

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
        {'support': 支撑位, 'resistance': 阻力位, 'current_position': 当前位置}
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)

    # 最近N期的最高价和最低价
    recent_high = high_prices.rolling(window=period).max().iloc[-1]
    recent_low = low_prices.rolling(window=period).min().iloc[-1]
    current_price = close_prices.iloc[-1]

    # 计算当前位置（0-1之间，0表示支撑位，1表示阻力位）
    price_range = recent_high - recent_low
    if price_range > 0:
        current_position = (current_price - recent_low) / price_range
    else:
        current_position = 0.5

    return {
        "support": float(recent_low),
        "resistance": float(recent_high),
        "current_position": float(current_position),
    }
