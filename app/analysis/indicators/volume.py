"""
成交量指标

实现成交量相关指标
"""

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def obv(
    close_prices: list[float] | pd.Series,
    volumes: list[float] | pd.Series,
) -> pd.Series:
    """
    能量潮指标 (On Balance Volume)

    Args:
        close_prices: 收盘价序列
        volumes: 成交量序列

    Returns:
        OBV序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    # 计算OBV
    obv_series = pd.Series(0.0, index=close_prices.index)

    for i in range(1, len(close_prices)):
        if close_prices.iloc[i] > close_prices.iloc[i - 1]:
            # 价格上涨，加上成交量
            obv_series.iloc[i] = obv_series.iloc[i - 1] + volumes.iloc[i]
        elif close_prices.iloc[i] < close_prices.iloc[i - 1]:
            # 价格下跌，减去成交量
            obv_series.iloc[i] = obv_series.iloc[i - 1] - volumes.iloc[i]
        else:
            # 价格不变，OBV不变
            obv_series.iloc[i] = obv_series.iloc[i - 1]

    return obv_series


def volume_ma(
    volumes: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    成交量移动平均

    Args:
        volumes: 成交量序列
        period: 周期

    Returns:
        成交量MA序列
    """
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    return volumes.rolling(window=period).mean()


def volume_ratio(
    volumes: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    量比 (当前成交量 / 平均成交量)

    Args:
        volumes: 成交量序列
        period: 周期

    Returns:
        量比序列
    """
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    avg_volume = volume_ma(volumes, period)

    return volumes / avg_volume


def money_flow_index(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volumes: list[float] | pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    资金流量指标 (Money Flow Index)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volumes: 成交量序列
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
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    # 典型价格
    tp = (high_prices + low_prices + close_prices) / 3

    # 资金流量 = 典型价格 * 成交量
    mf = tp * volumes

    # 正资金流量和负资金流量
    positive_mf = pd.Series(0.0, index=mf.index)
    negative_mf = pd.Series(0.0, index=mf.index)

    positive_mf[tp > tp.shift(1)] = mf
    negative_mf[tp < tp.shift(1)] = mf

    # 正负资金流量和
    positive_sum = positive_mf.rolling(window=period).sum()
    negative_sum = negative_mf.rolling(window=period).sum()

    # MFI = 100 - 100 / (1 + 正资金流量和 / 负资金流量和)
    mfi = 100 - (100 / (1 + positive_sum / negative_sum))

    return mfi


def accumulation_distribution(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volumes: list[float] | pd.Series,
) -> pd.Series:
    """
    累积/派发线 (Accumulation/Distribution Line)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volumes: 成交量序列

    Returns:
        A/D序列
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    # CLV = ((收盘 - 最低) - (最高 - 收盘)) / (最高 - 最低)
    clv = ((close_prices - low_prices) - (high_prices - close_prices)) / (
        high_prices - low_prices
    )

    # A/D = A/D前值 + CLV * 成交量
    ad = (clv * volumes).cumsum()

    return ad


def chaikin_money_flow(
    high_prices: list[float] | pd.Series,
    low_prices: list[float] | pd.Series,
    close_prices: list[float] | pd.Series,
    volumes: list[float] | pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    蔡金资金流量 (Chaikin Money Flow)

    Args:
        high_prices: 最高价序列
        low_prices: 最低价序列
        close_prices: 收盘价序列
        volumes: 成交量序列
        period: 周期

    Returns:
        CMF序列 (-1到1)
    """
    if isinstance(high_prices, list):
        high_prices = pd.Series(high_prices)
    if isinstance(low_prices, list):
        low_prices = pd.Series(low_prices)
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    # CLV
    clv = ((close_prices - low_prices) - (high_prices - close_prices)) / (
        high_prices - low_prices
    )

    # 资金流量
    mf = clv * volumes

    # CMF = N期资金流量和 / N期成交量
    mf_sum = mf.rolling(window=period).sum()
    vol_sum = volumes.rolling(window=period).sum()

    cmf = mf_sum / vol_sum

    return cmf


def volume_price_trend(
    close_prices: list[float] | pd.Series,
    volumes: list[float] | pd.Series,
) -> pd.Series:
    """
    量价趋势指标 (Volume Price Trend)

    Args:
        close_prices: 收盘价序列
        volumes: 成交量序列

    Returns:
        VPT序列
    """
    if isinstance(close_prices, list):
        close_prices = pd.Series(close_prices)
    if isinstance(volumes, list):
        volumes = pd.Series(volumes)

    # 价格变化率
    price_change_pct = close_prices.pct_change()

    # VPT = VPT前值 + 成交量 * 价格变化率
    vpt = (volumes * price_change_pct).cumsum()

    return vpt
