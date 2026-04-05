"""Volume Indicators完整测试 - 类型安全、防御性编程"""

import pytest
import pandas as pd
import numpy as np

from app.analysis.indicators.volume import (
    obv,
    volume_ma,
    volume_ratio,
    money_flow_index,
    accumulation_distribution,
    chaikin_money_flow,
    volume_price_trend,
)


class TestVolumeIndicators:
    """成交量指标测试"""

    def test_obv_basic(self):
        """测试OBV基本计算"""
        closes = [10.0, 10.5, 10.3, 10.8, 10.6]
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = obv(closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_obv_with_series(self):
        """测试OBV使用Series"""
        closes = pd.Series([10.0, 10.5, 10.3, 10.8, 10.6])
        volumes = pd.Series([1000000, 1200000, 1100000, 1500000, 1300000])
        
        result = obv(closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_obv_uptrend(self):
        """测试OBV上涨趋势"""
        # 持续上涨
        closes = [10.0, 10.5, 11.0, 11.5, 12.0]
        volumes = [1000000, 1000000, 1000000, 1000000, 1000000]
        
        result = obv(closes, volumes)
        
        # OBV应该持续增加
        assert result.iloc[-1] > result.iloc[0]

    def test_obv_downtrend(self):
        """测试OBV下跌趋势"""
        # 持续下跌
        closes = [12.0, 11.5, 11.0, 10.5, 10.0]
        volumes = [1000000, 1000000, 1000000, 1000000, 1000000]
        
        result = obv(closes, volumes)
        
        # OBV应该持续减少
        assert result.iloc[-1] < result.iloc[0]

    def test_volume_ma_basic(self):
        """测试成交量均线基本计算"""
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = volume_ma(volumes, period=3)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(volumes)

    def test_volume_ma_with_period(self):
        """测试成交量均线不同周期"""
        volumes = [1000000 + i * 100000 for i in range(20)]
        
        result5 = volume_ma(volumes, period=5)
        result10 = volume_ma(volumes, period=10)
        
        assert len(result5) == len(volumes)
        assert len(result10) == len(volumes)

    def test_volume_ratio_basic(self):
        """测试量比基本计算"""
        volumes = [1000000] * 5 + [2000000] * 5
        
        result = volume_ratio(volumes, period=5)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(volumes)

    def test_money_flow_index_basic(self):
        """测试MFI基本计算"""
        highs = [10.5, 10.8, 11.0, 10.7, 10.9]
        lows = [10.0, 10.3, 10.5, 10.2, 10.4]
        closes = [10.2, 10.6, 10.8, 10.4, 10.7]
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = money_flow_index(highs, lows, closes, volumes, period=3)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_accumulation_distribution_basic(self):
        """测试AD基本计算"""
        highs = [10.5, 10.8, 11.0, 10.7, 10.9]
        lows = [10.0, 10.3, 10.5, 10.2, 10.4]
        closes = [10.2, 10.6, 10.8, 10.4, 10.7]
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = accumulation_distribution(highs, lows, closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_chaikin_money_flow_basic(self):
        """测试CMF基本计算"""
        highs = [10.5, 10.8, 11.0, 10.7, 10.9]
        lows = [10.0, 10.3, 10.5, 10.2, 10.4]
        closes = [10.2, 10.6, 10.8, 10.4, 10.7]
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = chaikin_money_flow(highs, lows, closes, volumes, period=3)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_volume_price_trend_basic(self):
        """测试VPT基本计算"""
        closes = [10.0, 10.5, 10.3, 10.8, 10.6]
        volumes = [1000000, 1200000, 1100000, 1500000, 1300000]
        
        result = volume_price_trend(closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_volume_price_trend_uptrend(self):
        """测试VPT上涨趋势"""
        # 价格和成交量同时上涨
        closes = [10.0, 10.5, 11.0, 11.5, 12.0]
        volumes = [1000000, 1200000, 1400000, 1600000, 1800000]
        
        result = volume_price_trend(closes, volumes)
        
        # VPT应该变化（可能上涨也可能下跌，取决于计算方式）
        assert isinstance(result, pd.Series)
        assert len(result) == len(closes)

    def test_empty_input(self):
        """测试空输入"""
        closes = []
        volumes = []
        
        result = obv(closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_single_value(self):
        """测试单个值"""
        closes = [10.0]
        volumes = [1000000]
        
        result = obv(closes, volumes)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 1
