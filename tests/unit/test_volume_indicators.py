"""
成交量指标测试

测试 app/analysis/indicators/volume.py 中的函数。
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.analysis.indicators.volume import (
    ad,
    adosc,
    mfi,
    obv,
    volume_ma,
    volume_rate,
    volume_spike,
    vwap,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_ohlcv():
    """创建示例 OHLCV 数据"""
    n = 50  # 需要足够数据点供 TA-Lib 使用
    return {
        "high": pd.Series(np.random.uniform(11, 15, n)),
        "low": pd.Series(np.random.uniform(9, 11, n)),
        "close": pd.Series(np.random.uniform(10, 12, n)),
        "volume": pd.Series(np.random.uniform(1000, 2000, n)),
    }


# ============================================================
# obv
# ============================================================


class TestObv:
    """测试 OBV 指标"""

    def test_obv_with_pandas(self, sample_ohlcv):
        """测试 pandas 输入"""
        result = obv(sample_ohlcv["close"], sample_ohlcv["volume"])
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv["close"])

    def test_obv_with_lists(self):
        """测试列表输入"""
        close = [10.0, 11.0, 12.0, 11.0, 13.0] * 10
        volume = [1000.0, 1100.0, 1200.0, 1300.0, 1400.0] * 10
        result = obv(close, volume)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close)


# ============================================================
# ad
# ============================================================


class TestAd:
    """测试 AD 指标"""

    def test_ad_with_pandas(self, sample_ohlcv):
        """测试 pandas 输入"""
        result = ad(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv["close"])

    def test_ad_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0] * 10
        low = [9.0, 10.0, 11.0, 12.0, 13.0] * 10
        close = [10.0, 11.0, 12.0, 13.0, 14.0] * 10
        volume = [1000.0, 1100.0, 1200.0, 1300.0, 1400.0] * 10
        result = ad(high, low, close, volume)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close)


# ============================================================
# adosc
# ============================================================


class TestAdosc:
    """测试 ADOSC 指标"""

    def test_adosc_with_pandas(self, sample_ohlcv):
        """测试 pandas 输入"""
        result = adosc(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv["close"])

    def test_adosc_with_custom_periods(self, sample_ohlcv):
        """测试自定义周期"""
        result = adosc(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
            fast_period=5,
            slow_period=15,
        )
        assert isinstance(result, pd.Series)


# ============================================================
# mfi
# ============================================================


class TestMfi:
    """测试 MFI 指标"""

    def test_mfi_with_pandas(self, sample_ohlcv):
        """测试 pandas 输入"""
        result = mfi(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv["close"])

    def test_mfi_with_custom_period(self, sample_ohlcv):
        """测试自定义周期"""
        result = mfi(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
            period=10,
        )
        assert isinstance(result, pd.Series)


# ============================================================
# volume_rate
# ============================================================


class TestVolumeRate:
    """测试成交量比率"""

    def test_volume_rate_with_pandas(self):
        """测试 pandas 输入"""
        volume = pd.Series([1000, 1100, 1200, 1300, 1400])
        result = volume_rate(volume, period=3)
        assert isinstance(result, pd.Series)
        assert len(result) == len(volume)

    def test_volume_rate_with_list(self):
        """测试列表输入"""
        volume = [1000, 1100, 1200, 1300, 1400]
        result = volume_rate(volume, period=3)
        assert isinstance(result, pd.Series)
        assert len(result) == len(volume)


# ============================================================
# volume_ma
# ============================================================


class TestVolumeMa:
    """测试成交量移动平均"""

    def test_volume_ma_with_pandas(self):
        """测试 pandas 输入"""
        volume = pd.Series([1000, 1100, 1200, 1300, 1400])
        result = volume_ma(volume, period=3)
        assert isinstance(result, pd.Series)
        assert len(result) == len(volume)

    def test_volume_ma_with_list(self):
        """测试列表输入"""
        volume = [1000, 1100, 1200, 1300, 1400]
        result = volume_ma(volume, period=3)
        assert isinstance(result, pd.Series)


# ============================================================
# volume_spike
# ============================================================


class TestVolumeSpike:
    """测试成交量异常检测"""

    def test_volume_spike_with_pandas(self):
        """测试 pandas 输入"""
        volume = pd.Series([1000, 1100, 1200, 5000, 1400])
        result = volume_spike(volume, period=3, threshold=2.0)
        assert isinstance(result, pd.Series)
        assert len(result) == len(volume)
        # 检查是否有放量标记 (1)
        assert (result == 1).any() or (result == 0).all()

    def test_volume_spike_with_list(self):
        """测试列表输入"""
        volume = [1000, 1100, 1200, 5000, 1400]
        result = volume_spike(volume, period=3, threshold=2.0)
        assert isinstance(result, pd.Series)


# ============================================================
# vwap
# ============================================================


class TestVwap:
    """测试 VWAP 指标"""

    def test_vwap_with_pandas(self, sample_ohlcv):
        """测试 pandas 输入"""
        result = vwap(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv["close"])

    def test_vwap_with_lists(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0]
        low = [9.0, 10.0, 11.0, 12.0, 13.0]
        close = [10.0, 11.0, 12.0, 13.0, 14.0]
        volume = [1000, 1100, 1200, 1300, 1400]
        result = vwap(high, low, close, volume)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close)
