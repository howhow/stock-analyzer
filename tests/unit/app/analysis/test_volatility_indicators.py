"""
波动率指标测试

测试 app/analysis/indicators/volatility.py 中的函数。
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.analysis.indicators.volatility import (
    adx,
    atr,
    bollinger_bands,
    donchian_channel,
    historical_volatility,
    keltner_channel,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_ohlc():
    """创建示例 OHLC 数据"""
    n = 50
    return {
        "high": pd.Series(np.random.uniform(11, 15, n)),
        "low": pd.Series(np.random.uniform(9, 11, n)),
        "close": pd.Series(np.random.uniform(10, 12, n)),
    }


# ============================================================
# atr
# ============================================================


class TestAtr:
    """测试 ATR 指标"""

    def test_atr_with_pandas(self, sample_ohlc):
        """测试 pandas 输入"""
        result = atr(sample_ohlc["high"], sample_ohlc["low"], sample_ohlc["close"])
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlc["close"])

    def test_atr_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0] * 10
        low = [9.0, 10.0, 11.0, 12.0, 13.0] * 10
        close = [10.0, 11.0, 12.0, 13.0, 14.0] * 10
        result = atr(high, low, close)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close)


# ============================================================
# adx
# ============================================================


class TestAdx:
    """测试 ADX 指标"""

    def test_adx_with_pandas(self, sample_ohlc):
        """测试 pandas 输入"""
        result = adx(sample_ohlc["high"], sample_ohlc["low"], sample_ohlc["close"])
        assert isinstance(result, dict)
        assert "adx" in result
        assert "plus_di" in result
        assert "minus_di" in result
        assert len(result["adx"]) == len(sample_ohlc["close"])

    def test_adx_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0] * 10
        low = [9.0, 10.0, 11.0, 12.0, 13.0] * 10
        close = [10.0, 11.0, 12.0, 13.0, 14.0] * 10
        result = adx(high, low, close)
        assert isinstance(result, dict)


# ============================================================
# bollinger_bands
# ============================================================


class TestBollingerBands:
    """测试布林通道"""

    def test_bollinger_bands_with_pandas(self, sample_ohlc):
        """测试 pandas 输入"""
        result = bollinger_bands(sample_ohlc["close"])
        assert isinstance(result, dict)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert "width" in result
        assert len(result["upper"]) == len(sample_ohlc["close"])

    def test_bollinger_bands_with_list(self):
        """测试列表输入"""
        close = [10.0, 11.0, 12.0, 11.0, 13.0] * 10
        result = bollinger_bands(close, period=5, std_dev=1.5)
        assert isinstance(result, dict)


# ============================================================
# historical_volatility
# ============================================================


class TestHistoricalVolatility:
    """测试历史波动率"""

    def test_historical_volatility_with_pandas(self):
        """测试 pandas 输入"""
        close = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0] * 10)
        result = historical_volatility(close, period=5)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close)

    def test_historical_volatility_with_list(self):
        """测试列表输入"""
        close = [10.0, 11.0, 12.0, 11.0, 13.0] * 10
        result = historical_volatility(close, period=5)
        assert isinstance(result, pd.Series)


# ============================================================
# keltner_channel
# ============================================================


class TestKeltnerChannel:
    """测试肯特纳通道"""

    def test_keltner_channel_with_pandas(self, sample_ohlc):
        """测试 pandas 输入"""
        result = keltner_channel(
            sample_ohlc["high"], sample_ohlc["low"], sample_ohlc["close"]
        )
        assert isinstance(result, dict)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert len(result["upper"]) == len(sample_ohlc["close"])

    def test_keltner_channel_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0] * 10
        low = [9.0, 10.0, 11.0, 12.0, 13.0] * 10
        close = [10.0, 11.0, 12.0, 13.0, 14.0] * 10
        result = keltner_channel(high, low, close)
        assert isinstance(result, dict)


# ============================================================
# donchian_channel
# ============================================================


class TestDonchianChannel:
    """测试唐奇安通道"""

    def test_donchian_channel_with_pandas(self, sample_ohlc):
        """测试 pandas 输入"""
        result = donchian_channel(sample_ohlc["high"], sample_ohlc["low"])
        assert isinstance(result, dict)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert len(result["upper"]) == len(sample_ohlc["high"])

    def test_donchian_channel_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0] * 10
        low = [9.0, 10.0, 11.0, 12.0, 13.0] * 10
        result = donchian_channel(high, low)
        assert isinstance(result, dict)
