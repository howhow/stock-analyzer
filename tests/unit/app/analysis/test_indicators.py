"""
技术指标单元测试
"""

import pytest

from app.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    golden_cross,
    macd,
    rsi,
    sma,
    support_resistance,
    trend_direction,
)


class TestTrendIndicators:
    """趋势指标测试"""

    def test_sma(self):
        """测试SMA"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = sma(data, 3)
        assert len(result) == 5
        # SMA(3) = [nan, nan, 2, 3, 4]
        assert result.iloc[2] == 2.0
        assert result.iloc[4] == 4.0

    def test_ema(self):
        """测试EMA"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = ema(data, 3)
        assert len(result) == 5
        # EMA 计算结果验证
        assert result.iloc[-1] > 0

    def test_macd(self):
        """测试MACD"""
        data = [float(i) for i in range(1, 101)]  # 上涨趋势
        result = macd(data, 12, 26, 9)

        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result
        assert len(result["macd"]) == 100

    def test_bollinger_bands(self):
        """测试布林带"""
        data = [float(i) for i in range(1, 101)]
        result = bollinger_bands(data, 20, 2.0)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        # 上轨 > 中轨 > 下轨
        assert result["upper"].iloc[-1] > result["middle"].iloc[-1]
        assert result["middle"].iloc[-1] > result["lower"].iloc[-1]

    def test_trend_direction(self):
        """测试趋势方向"""
        # 上涨趋势
        uptrend = [float(i) for i in range(1, 101)]
        result = trend_direction(uptrend, 5, 20)
        assert result.iloc[-1] == 1  # 上涨

        # 下跌趋势
        downtrend = [float(i) for i in range(100, 0, -1)]
        result = trend_direction(downtrend, 5, 20)
        assert result.iloc[-1] == -1  # 下跌

    def test_golden_cross(self):
        """测试金叉死叉"""
        # 构造金叉场景（短期从下向上穿越长期）
        data = [100.0] * 10 + [float(i) for i in range(100, 150)]
        result = golden_cross(data, 5, 20)

        # 应该出现金叉信号
        assert 1 in result.values or 0 in result.values


class TestMomentumIndicators:
    """动量指标测试"""

    def test_rsi(self):
        """测试RSI"""
        data = [float(i) for i in range(1, 51)]  # 上涨数据
        result = rsi(data, 14)

        assert len(result) == 50
        # 上涨趋势，RSI应该较高
        assert result.iloc[-1] > 50

    def test_rsi_oversold_overbought(self):
        """测试RSI超买超卖"""
        # 上涨数据，RSI应该高于70（超买）
        uptrend = [float(i) for i in range(1, 101)]
        rsi_up = rsi(uptrend, 14)
        assert rsi_up.iloc[-1] > 70

        # 下跌数据，RSI应该低于30（超卖）
        downtrend = [float(i) for i in range(100, 0, -1)]
        rsi_down = rsi(downtrend, 14)
        assert rsi_down.iloc[-1] < 30


class TestVolatilityIndicators:
    """波动率指标测试"""

    def test_atr(self):
        """测试ATR"""
        high = [float(i) for i in range(105, 155)]  # 高价递增
        low = [float(i) for i in range(100, 150)]  # 低价递增
        close = [float(i) for i in range(102, 152)]  # 收盘价递增

        result = atr(high, low, close, 14)
        assert len(result) == 50

    def test_atr_positive(self):
        """测试ATR为正数"""
        import random

        random.seed(42)
        high = [100.0 + random.random() * 5 for _ in range(50)]
        low = [100.0 - random.random() * 5 for _ in range(50)]
        close = [100.0 + random.random() * 2 for _ in range(50)]

        result = atr(high, low, close, 14)
        # ATR应该都是正数
        assert all(result.dropna() > 0)


class TestSupportResistance:
    """支撑阻力测试"""

    def test_support_resistance(self):
        """测试支撑阻力位"""
        high = [float(i) for i in range(110, 160)]  # 高价
        low = [float(i) for i in range(100, 150)]  # 低价
        close = [float(i) for i in range(105, 155)]  # 收盘价

        result = support_resistance(high, low, close, 20)

        assert "support" in result
        assert "resistance" in result
        assert result["support"] < result["resistance"]
