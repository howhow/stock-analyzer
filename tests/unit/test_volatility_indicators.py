"""Volatility Indicators完整测试 - 类型安全、防御性编程"""

import pytest
import pandas as pd
import numpy as np

from app.analysis.indicators.volatility import (
    atr,
    atr_percentage,
    volatility,
    keltner_channels,
    volatility_regime,
)


class TestVolatilityIndicators:
    """波动率指标测试"""

    def test_atr_basic(self):
        """测试ATR基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = atr(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_atr_with_series(self):
        """测试ATR使用Series"""
        highs = pd.Series([10.5 + i * 0.1 for i in range(30)])
        lows = pd.Series([10.0 + i * 0.1 for i in range(30)])
        closes = pd.Series([10.2 + i * 0.1 for i in range(30)])

        result = atr(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_atr_positive(self):
        """测试ATR为正值"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]

        result = atr(highs, lows, closes, period=14)

        # ATR应该为正
        valid_results = result.dropna()
        assert all(val >= 0 for val in valid_results)

    def test_atr_high_volatility(self):
        """测试高波动性ATR"""
        # 高波动性数据
        highs = [10.0 + i % 10 * 0.5 for i in range(30)]
        lows = [10.0 - i % 10 * 0.5 for i in range(30)]
        closes = [10.0 + (i % 10 - 5) * 0.2 for i in range(30)]

        result = atr(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_atr_percentage_basic(self):
        """测试ATR百分比基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = atr_percentage(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_atr_percentage_range(self):
        """测试ATR百分比范围"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]

        result = atr_percentage(highs, lows, closes, period=14)

        # ATR百分比应该为正
        valid_results = result.dropna()
        assert all(val >= 0 for val in valid_results)

    def test_volatility_basic(self):
        """测试波动率基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = volatility(closes, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_volatility_with_series(self):
        """测试波动率使用Series"""
        closes = pd.Series([10.0 + i * 0.1 for i in range(30)])

        result = volatility(closes, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_volatility_high(self):
        """测试高波动率"""
        # 高波动性数据
        closes = [10.0 + (i % 10 - 5) * 0.5 for i in range(50)]

        result = volatility(closes, period=20)

        # 波动率应该较高
        valid_results = result.dropna()
        if len(valid_results) > 0:
            assert valid_results.iloc[-1] > 0

    def test_keltner_channels_basic(self):
        """测试肯特纳通道基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = keltner_channels(highs, lows, closes, period=14)

        assert isinstance(result, dict)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

    def test_keltner_channels_relationship(self):
        """测试肯特纳通道关系"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]

        result = keltner_channels(highs, lows, closes, period=14)

        # 上轨 > 中轨 > 下轨
        upper = result["upper"].dropna()
        middle = result["middle"].dropna()
        lower = result["lower"].dropna()

        if len(upper) > 0 and len(middle) > 0 and len(lower) > 0:
            assert upper.iloc[-1] > middle.iloc[-1]
            assert middle.iloc[-1] > lower.iloc[-1]

    def test_volatility_regime_basic(self):
        """测试波动率机制基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = volatility_regime(closes, short_period=10, long_period=60)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_empty_input(self):
        """测试空输入"""
        highs = []
        lows = []
        closes = []

        result = atr(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_single_value(self):
        """测试单个值"""
        highs = [10.5]
        lows = [10.0]
        closes = [10.2]

        result = atr(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == 1
