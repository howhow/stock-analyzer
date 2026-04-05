"""Momentum Indicators完整测试 - 类型安全、防御性编程"""

import pytest
import pandas as pd
import numpy as np

from app.analysis.indicators.momentum import (
    rsi,
    rsi_signal,
    stochastic_oscillator,
    williams_r,
    momentum,
    rate_of_change,
    cci,
)


class TestMomentumIndicators:
    """动量指标测试"""

    def test_rsi_basic(self):
        """测试RSI基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = rsi(closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_rsi_with_series(self):
        """测试RSI使用Series"""
        closes = pd.Series([10.0 + i * 0.1 for i in range(30)])

        result = rsi(closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_rsi_range(self):
        """测试RSI范围（0-100）"""
        closes = [10.0 + np.sin(i * 0.2) * 2 for i in range(50)]

        result = rsi(closes, period=14)

        # RSI应该在0-100之间
        valid_results = result.dropna()
        assert all(0 <= val <= 100 for val in valid_results)

    def test_rsi_overbought(self):
        """测试RSI超买"""
        # 持续上涨
        closes = [10.0 + i * 1.0 for i in range(30)]

        result = rsi(closes, period=14)

        # RSI应该接近100（超买）
        assert result.iloc[-1] > 70

    def test_rsi_oversold(self):
        """测试RSI超卖"""
        # 持续下跌
        closes = [30.0 - i * 1.0 for i in range(30)]

        result = rsi(closes, period=14)

        # RSI应该接近0（超卖）
        assert result.iloc[-1] < 30

    def test_rsi_signal_basic(self):
        """测试RSI信号基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = rsi_signal(closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_stochastic_oscillator_basic(self):
        """测试随机指标基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = stochastic_oscillator(highs, lows, closes, k_period=14)

        # 返回字典，包含k和d两个Series
        assert isinstance(result, dict)
        assert "k" in result
        assert "d" in result
        assert isinstance(result["k"], pd.Series)
        assert len(result["k"]) == len(closes)

    def test_stochastic_oscillator_range(self):
        """测试随机指标范围（0-100）"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]

        result = stochastic_oscillator(highs, lows, closes, k_period=14)

        # K值应该在0-100之间
        valid_results = result["k"].dropna()
        assert all(0 <= val <= 100 for val in valid_results)

    def test_williams_r_basic(self):
        """测试威廉指标基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = williams_r(highs, lows, closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_williams_r_range(self):
        """测试威廉指标范围（-100 to 0）"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]

        result = williams_r(highs, lows, closes, period=14)

        # 威廉指标应该在-100到0之间
        valid_results = result.dropna()
        assert all(-100 <= val <= 0 for val in valid_results)

    def test_momentum_basic(self):
        """测试动量基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = momentum(closes, period=10)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_momentum_uptrend(self):
        """测试动量上涨趋势"""
        closes = [10.0 + i * 0.5 for i in range(30)]

        result = momentum(closes, period=10)

        # 动量应该为正
        assert result.iloc[-1] > 0

    def test_momentum_downtrend(self):
        """测试动量下跌趋势"""
        closes = [30.0 - i * 0.5 for i in range(30)]

        result = momentum(closes, period=10)

        # 动量应该为负
        assert result.iloc[-1] < 0

    def test_rate_of_change_basic(self):
        """测试变化率基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]

        result = rate_of_change(closes, period=10)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_cci_basic(self):
        """测试CCI基本计算"""
        highs = [10.5 + i * 0.1 for i in range(30)]
        lows = [10.0 + i * 0.1 for i in range(30)]
        closes = [10.2 + i * 0.1 for i in range(30)]

        result = cci(highs, lows, closes, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_empty_input(self):
        """测试空输入"""
        closes = []

        result = rsi(closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_single_value(self):
        """测试单个值"""
        closes = [10.0]

        result = rsi(closes, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == 1
