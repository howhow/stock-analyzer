"""五行识别器单元测试

测试目标:
- 木/火/金/水识别器核心逻辑
- 置信度计算
- 边界情况
"""

import numpy as np
import pandas as pd
import pytest

from framework.trading.wuxing.detectors import (
    DetectionResult,
    FireStateDetector,
    MetalStateDetector,
    WaterStateDetector,
    WoodStateDetector,
    WuxingElement,
)


class TestWoodStateDetector:
    """木形态识别器测试"""

    def _create_df(self, prices: list[float]) -> pd.DataFrame:
        """创建测试 DataFrame"""
        return pd.DataFrame(
            {
                "close": prices,
                "volume": [1000] * len(prices),
            }
        )

    def test_detect_wood_all_conditions_met(self) -> None:
        """测试木形态 — 所有条件满足"""
        detector = WoodStateDetector()
        df = self._create_df([100.0] * 60)

        result = detector.detect(
            df=df,
            current_price=70.0,  # 距高点 -30%
            historical_high=100.0,
            avg_volume_20d=1000.0,
            current_volume=2500.0,  # 2.5 倍放量
        )

        assert result.element == WuxingElement.WOOD
        assert result.confidence >= 0.7
        assert len(result.reasons) >= 3

    def test_detect_wood_partial_conditions(self) -> None:
        """测试木形态 — 部分条件满足"""
        detector = WoodStateDetector()
        df = self._create_df([100.0] * 60)

        result = detector.detect(
            df=df,
            current_price=70.0,
            historical_high=100.0,
            avg_volume_20d=1000.0,
            current_volume=1500.0,  # 1.5 倍（不满足 2-3 倍）
        )

        assert result.element == WuxingElement.WOOD
        # 只有 2 个条件满足，置信度中等
        assert 0.4 <= result.confidence <= 0.7

    def test_detect_not_wood(self) -> None:
        """测试不满足木形态"""
        detector = WoodStateDetector()
        df = self._create_df([100.0] * 60)

        result = detector.detect(
            df=df,
            current_price=95.0,  # 只回撤 5%
            historical_high=100.0,
            avg_volume_20d=1000.0,
            current_volume=1000.0,
        )

        assert result.element == WuxingElement.WOOD
        # EMA 收敛条件满足（价格平稳），但无回撤无放量
        # 只有 1 个条件满足，置信度低
        assert result.confidence < 0.6
        assert len(result.reasons) == 1  # 只有 EMA 收敛


class TestFireStateDetector:
    """火形态识别器测试"""

    def _create_df(self, prices: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "close": prices,
                "volume": [1000] * len(prices),
            }
        )

    def test_detect_fire_all_conditions(self) -> None:
        """测试火形态 — 所有条件满足"""
        detector = FireStateDetector()
        # 创建120个数据点用于EMA120计算
        prices = [80.0] * 120
        df = self._create_df(prices)

        result = detector.detect(
            df=df,
            current_price=100.0,  # 突破 EMA120
            recent_low=70.0,  # 从低点上涨 42%
            avg_volume_20d=1000.0,
            current_volume=4000.0,  # 4 倍放量
        )

        assert result.element == WuxingElement.FIRE
        assert result.confidence >= 0.7
        assert len(result.reasons) >= 3

    def test_detect_fire_breakout_only(self) -> None:
        """测试火形态 — 仅突破"""
        detector = FireStateDetector()
        prices = [80.0] * 120
        df = self._create_df(prices)

        result = detector.detect(
            df=df,
            current_price=100.0,
            recent_low=90.0,  # 突破幅度小
            avg_volume_20d=1000.0,
            current_volume=1000.0,  # 无量
        )

        assert result.element == WuxingElement.FIRE
        # 只有突破EMA，置信度低
        assert result.confidence < 0.6


class TestMetalStateDetector:
    """金形态识别器测试"""

    def _create_df(self, prices: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "close": prices,
                "volume": [1000] * len(prices),
            }
        )

    def test_detect_metal_drop(self) -> None:
        """测试金形态 — 放量跌"""
        detector = MetalStateDetector()
        df = self._create_df([100.0] * 30)

        result = detector.detect(
            df=df,
            current_price=94.0,
            recent_high=100.0,
            recent_low=80.0,
            avg_volume_20d=1000.0,
            current_volume=2000.0,  # 2 倍放量
            daily_change=-0.06,  # 跌 6%
        )

        assert result.element == WuxingElement.METAL
        assert result.confidence >= 0.5
        assert any("放量跌" in r for r in result.reasons)

    def test_detect_metal_fibonacci(self) -> None:
        """测试金形态 — 斐波那契回落"""
        detector = MetalStateDetector()
        df = self._create_df([100.0] * 30)

        # 高点 100，低点 80，当前 92.4（约 38.2% 回落）
        result = detector.detect(
            df=df,
            current_price=92.4,
            recent_high=100.0,
            recent_low=80.0,
            avg_volume_20d=1000.0,
            current_volume=1000.0,
            daily_change=-0.01,
        )

        assert result.element == WuxingElement.METAL
        assert any("斐波那契" in r for r in result.reasons)


class TestWaterStateDetector:
    """水形态识别器测试"""

    def _create_df(self, prices: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "close": prices,
                "volume": [1000] * len(prices),
            }
        )

    def test_detect_water_all_conditions(self) -> None:
        """测试水形态 — 连续跌 + 缩量"""
        detector = WaterStateDetector()
        df = self._create_df([100.0] * 30)

        result = detector.detect(
            df=df,
            current_price=92.0,  # 5日跌 8%
            price_n_days_ago=100.0,
            avg_volume_20d=1000.0,
            current_volume=400.0,  # 缩量至 40%
        )

        assert result.element == WuxingElement.WATER
        assert result.confidence >= 0.5
        assert len(result.reasons) >= 2

    def test_detect_water_not_enough_drop(self) -> None:
        """测试水形态 — 跌幅不够"""
        detector = WaterStateDetector()
        df = self._create_df([100.0] * 30)

        result = detector.detect(
            df=df,
            current_price=98.0,  # 只跌 2%
            price_n_days_ago=100.0,
            avg_volume_20d=1000.0,
            current_volume=400.0,
        )

        assert result.element == WuxingElement.WATER
        # 只有缩量，置信度低
        assert result.confidence < 0.6


class TestDetectionResult:
    """DetectionResult 数据模型测试"""

    def test_is_confident_true(self) -> None:
        """测试高置信度"""
        result = DetectionResult(
            element=WuxingElement.WOOD,
            confidence=0.8,
        )
        assert result.is_confident is True

    def test_is_confident_false(self) -> None:
        """测试低置信度"""
        result = DetectionResult(
            element=WuxingElement.SOIL,
            confidence=0.5,
        )
        assert result.is_confident is False
