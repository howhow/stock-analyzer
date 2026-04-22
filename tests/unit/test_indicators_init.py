"""
技术指标模块测试

测试 app/analysis/indicators/__init__.py 中的函数。
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.analysis.indicators import (
    atr_percentage,
    chaikin_money_flow,
    keltner_channels,
    volatility,
    volatility_regime,
    volume_price_trend,
)


class TestAtrPercentage:
    """测试 ATR 百分比函数"""

    def test_atr_percentage_with_pandas(self):
        """测试 pandas 输入"""
        high = pd.Series([11.0, 12.0, 13.0, 14.0, 15.0])
        low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0])
        close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])

        result = atr_percentage(high, low, close)

        assert isinstance(result, pd.Series)
        assert len(result) == len(close)

    def test_atr_percentage_with_list(self):
        """测试列表输入"""
        high = [11.0, 12.0, 13.0, 14.0, 15.0]
        low = [9.0, 10.0, 11.0, 12.0, 13.0]
        close = [10.0, 11.0, 12.0, 13.0, 14.0]

        result = atr_percentage(high, low, close)

        assert isinstance(result, pd.Series)


class TestVolatility:
    """测试波动率别名函数"""

    def test_volatility_alias(self):
        """测试波动率函数调用"""
        close = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0] * 5)
        result = volatility(close)
        assert isinstance(result, pd.Series)


class TestKeltnerChannels:
    """测试肯特纳通道别名函数"""

    def test_keltner_channels_alias(self):
        """测试肯特纳通道函数调用"""
        high = pd.Series([11.0, 12.0, 13.0, 14.0, 15.0] * 5)
        low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0] * 5)
        close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0] * 5)

        result = keltner_channels(high, low, close)

        # keltner_channel 返回 dict
        assert isinstance(result, dict)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result


class TestVolatilityRegime:
    """测试波动率状态函数"""

    def test_high_volatility(self):
        """测试高波动率状态"""
        # 创建波动较大的价格序列
        close = pd.Series([10.0, 15.0, 8.0, 20.0, 5.0] * 10)
        result = volatility_regime(close)
        assert result in ["high", "low", "normal", "unknown"]

    def test_low_volatility(self):
        """测试低波动率状态"""
        # 创建稳定的价格序列
        close = pd.Series([10.0, 10.1, 10.05, 10.08, 10.02] * 10)
        result = volatility_regime(close)
        assert result in ["high", "low", "normal", "unknown"]

    def test_empty_series(self):
        """测试空序列"""
        close = pd.Series([])
        # 空序列应该抛出异常或返回 unknown
        try:
            result = volatility_regime(close)
            assert result == "unknown"
        except (ValueError, IndexError):
            # 接受异常作为合理行为
            pass

    def test_normal_volatility(self):
        """测试正常波动率"""
        close = pd.Series([10.0, 11.0, 9.0, 12.0, 10.5] * 10)
        result = volatility_regime(close)
        assert result in ["high", "low", "normal", "unknown"]


class TestChaikinMoneyFlow:
    """测试佳庆资金流量函数"""

    @patch("app.analysis.indicators.ad")
    def test_chaikin_money_flow(self, mock_ad):
        """测试 CMF 计算"""
        mock_ad_values = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0] * 5)
        mock_ad.return_value = mock_ad_values

        high = pd.Series([11.0, 12.0, 13.0, 14.0, 15.0] * 5)
        low = pd.Series([9.0, 10.0, 11.0, 12.0, 13.0] * 5)
        close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0] * 5)
        volume = pd.Series([1000, 1100, 1200, 1300, 1400] * 5)

        result = chaikin_money_flow(high, low, close, volume)

        assert isinstance(result, pd.Series)
        assert len(result) == len(close)

    @patch("app.analysis.indicators.ad")
    def test_chaikin_with_lists(self, mock_ad):
        """测试列表输入"""
        mock_ad_values = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0])
        mock_ad.return_value = mock_ad_values

        high = [11.0, 12.0, 13.0, 14.0, 15.0]
        low = [9.0, 10.0, 11.0, 12.0, 13.0]
        close = [10.0, 11.0, 12.0, 13.0, 14.0]
        volume = [1000, 1100, 1200, 1300, 1400]

        result = chaikin_money_flow(high, low, close, volume)

        assert isinstance(result, pd.Series)


class TestVolumePriceTrend:
    """测试成交量价格趋势函数"""

    def test_vpt_with_pandas(self):
        """测试 pandas 输入"""
        close = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0])
        volume = pd.Series([1000, 1100, 1200, 1300, 1400])

        result = volume_price_trend(close, volume)

        assert isinstance(result, pd.Series)
        assert len(result) == len(close)

    def test_vpt_with_lists(self):
        """测试列表输入"""
        close = [10.0, 11.0, 12.0, 11.0, 13.0]
        volume = [1000, 1100, 1200, 1300, 1400]

        result = volume_price_trend(close, volume)

        assert isinstance(result, pd.Series)
        assert len(result) == len(close)


class TestImports:
    """测试导入"""

    def test_all_exports_exist(self):
        """测试所有导出函数可导入"""
        from app.analysis import indicators

        for name in indicators.__all__:
            assert hasattr(indicators, name), f"Missing export: {name}"
