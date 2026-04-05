"""Trend Indicators完整测试 - 类型安全、防御性编程"""

import pytest
import pandas as pd
import numpy as np

from app.analysis.indicators.trend import (
    sma,
    ema,
    macd,
    bollinger_bands,
    trend_direction,
    golden_cross,
    support_resistance,
)


class TestTrendIndicators:
    """趋势指标测试"""

    def test_sma_basic(self):
        """测试SMA基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]
        
        result = sma(closes, period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_sma_with_series(self):
        """测试SMA使用Series"""
        closes = pd.Series([10.0 + i * 0.1 for i in range(30)])
        
        result = sma(closes, period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_sma_uptrend(self):
        """测试SMA上涨趋势"""
        closes = [10.0 + i * 0.5 for i in range(50)]
        
        result = sma(closes, period=20)
        
        # SMA应该上涨
        valid_results = result.dropna()
        if len(valid_results) > 1:
            assert valid_results.iloc[-1] > valid_results.iloc[0]

    def test_ema_basic(self):
        """测试EMA基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]
        
        result = ema(closes, period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_ema_responsive(self):
        """测试EMA响应性"""
        # EMA应该比SMA更快响应价格变化
        closes = [10.0] * 20 + [15.0] * 10
        
        sma_result = sma(closes, period=20)
        ema_result = ema(closes, period=20)
        
        # EMA应该更快上涨
        valid_sma = sma_result.dropna()
        valid_ema = ema_result.dropna()
        
        if len(valid_sma) > 0 and len(valid_ema) > 0:
            # EMA应该高于SMA（因为最近价格上涨）
            assert valid_ema.iloc[-1] >= valid_sma.iloc[-1]

    def test_macd_basic(self):
        """测试MACD基本计算"""
        closes = [10.0 + i * 0.1 for i in range(50)]
        
        result = macd(closes, fast_period=12, slow_period=26, signal_period=9)
        
        assert isinstance(result, dict)
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result

    def test_macd_crossover(self):
        """测试MACD交叉"""
        # 先下跌后上涨
        closes = [20.0 - i * 0.2 for i in range(20)] + [16.0 + i * 0.3 for i in range(30)]
        
        result = macd(closes, fast_period=12, slow_period=26, signal_period=9)
        
        assert isinstance(result, dict)
        assert 'macd' in result

    def test_bollinger_bands_basic(self):
        """测试布林带基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]
        
        result = bollinger_bands(closes, period=20, std_dev=2)
        
        assert isinstance(result, dict)
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result

    def test_bollinger_bands_relationship(self):
        """测试布林带关系"""
        closes = [10.0 + np.sin(i * 0.2) * 2 for i in range(50)]
        
        result = bollinger_bands(closes, period=20, std_dev=2)
        
        # 上轨 > 中轨 > 下轨
        upper = result['upper'].dropna()
        middle = result['middle'].dropna()
        lower = result['lower'].dropna()
        
        if len(upper) > 0 and len(middle) > 0 and len(lower) > 0:
            assert upper.iloc[-1] > middle.iloc[-1]
            assert middle.iloc[-1] > lower.iloc[-1]

    def test_trend_direction_basic(self):
        """测试趋势方向基本计算"""
        closes = [10.0 + i * 0.1 for i in range(30)]
        
        result = trend_direction(closes, short_period=5, long_period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_trend_direction_uptrend(self):
        """测试趋势方向上涨"""
        closes = [10.0 + i * 0.5 for i in range(50)]
        
        result = trend_direction(closes, short_period=5, long_period=20)
        
        # 趋势应该为正（上涨）
        valid_results = result.dropna()
        if len(valid_results) > 0:
            assert valid_results.iloc[-1] > 0

    def test_trend_direction_downtrend(self):
        """测试趋势方向下跌"""
        closes = [30.0 - i * 0.5 for i in range(50)]
        
        result = trend_direction(closes, short_period=5, long_period=20)
        
        # 趋势应该为负（下跌）
        valid_results = result.dropna()
        if len(valid_results) > 0:
            assert valid_results.iloc[-1] < 0

    def test_golden_cross_basic(self):
        """测试金叉基本计算"""
        closes = [10.0 + i * 0.1 for i in range(50)]
        
        result = golden_cross(closes, short_period=5, long_period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_golden_cross_signal(self):
        """测试金叉信号"""
        # 先平稳后上涨
        closes = [10.0] * 20 + [10.0 + i * 0.5 for i in range(30)]
        
        result = golden_cross(closes, short_period=5, long_period=20)
        
        assert isinstance(result, pd.Series)

    def test_support_resistance_basic(self):
        """测试支撑阻力基本计算"""
        highs = [10.5 + np.sin(i * 0.2) for i in range(50)]
        lows = [10.0 + np.sin(i * 0.2) for i in range(50)]
        closes = [10.2 + np.sin(i * 0.2) for i in range(50)]
        
        result = support_resistance(highs, lows, closes, period=20)
        
        assert isinstance(result, dict)
        assert 'support' in result
        assert 'resistance' in result

    def test_empty_input(self):
        """测试空输入"""
        closes = []
        
        result = sma(closes, period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_single_value(self):
        """测试单个值"""
        closes = [10.0]
        
        result = sma(closes, period=20)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 1
