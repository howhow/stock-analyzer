"""安全边际模块单元测试

测试目标:
- 安全边际计算
- β 系数动态调整
- PE/PB 分位辅助判断
- 等级分类
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from framework.trading.seasons.safety_margin import (
    DEFAULT_THRESHOLDS,
    MarginLevel,
    SafetyMarginCalculator,
    SafetyMarginResult,
)


class TestSafetyMarginCalculator:
    """SafetyMarginCalculator 核心功能测试"""

    def test_initialization(self) -> None:
        """测试初始化"""
        calc = SafetyMarginCalculator()
        assert calc._thresholds == DEFAULT_THRESHOLDS

    def test_initialization_with_custom_thresholds(self) -> None:
        """测试自定义阈值"""
        custom = {"deeply_undervalued": 0.50}
        calc = SafetyMarginCalculator(thresholds=custom)
        assert calc._thresholds["deeply_undervalued"] == 0.50

    def test_calculate_margin_positive(self) -> None:
        """测试安全边际计算 — 正值（低估）"""
        calc = SafetyMarginCalculator()
        margin = calc.calculate_margin(dcf_value=120.0, current_price=100.0)
        assert margin == pytest.approx(0.20, rel=0.01)

    def test_calculate_margin_negative(self) -> None:
        """测试安全边际计算 — 负值（高估）"""
        calc = SafetyMarginCalculator()
        margin = calc.calculate_margin(dcf_value=80.0, current_price=100.0)
        assert margin == pytest.approx(-0.20, rel=0.01)

    def test_calculate_margin_zero_price(self) -> None:
        """测试价格为 0 时的安全边际"""
        calc = SafetyMarginCalculator()
        margin = calc.calculate_margin(dcf_value=100.0, current_price=0.0)
        assert margin == 0.0

    def test_classify_level_deeply_undervalued(self) -> None:
        """测试等级分类 — 极度低估"""
        calc = SafetyMarginCalculator()
        level = calc.classify_level(
            safety_margin=0.50, adjusted_thresholds=DEFAULT_THRESHOLDS
        )
        assert level == MarginLevel.DEEPLY_UNDERVALUED

    def test_classify_level_undervalued(self) -> None:
        """测试等级分类 — 低估"""
        calc = SafetyMarginCalculator()
        level = calc.classify_level(
            safety_margin=0.25, adjusted_thresholds=DEFAULT_THRESHOLDS
        )
        assert level == MarginLevel.UNDERVALUED

    def test_classify_level_fair(self) -> None:
        """测试等级分类 — 合理"""
        calc = SafetyMarginCalculator()
        level = calc.classify_level(
            safety_margin=0.05, adjusted_thresholds=DEFAULT_THRESHOLDS
        )
        assert level == MarginLevel.FAIR

    def test_classify_level_overvalued(self) -> None:
        """测试等级分类 — 高估"""
        calc = SafetyMarginCalculator()
        level = calc.classify_level(
            safety_margin=-0.15, adjusted_thresholds=DEFAULT_THRESHOLDS
        )
        assert level == MarginLevel.OVERVALUED

    def test_classify_level_deeply_overvalued(self) -> None:
        """测试等级分类 — 极度高估"""
        calc = SafetyMarginCalculator()
        level = calc.classify_level(
            safety_margin=-0.30, adjusted_thresholds=DEFAULT_THRESHOLDS
        )
        assert level == MarginLevel.DEEPLY_OVERVALUED


class TestBetaAdjustment:
    """β 系数动态调整测试"""

    def test_high_beta_adjustment(self) -> None:
        """测试高 β 系数调整（β > 1.5）"""
        calc = SafetyMarginCalculator()
        adjusted = calc._adjust_thresholds(beta=2.0)

        # 高 β 应该放大阈值
        assert adjusted["deeply_undervalued"] > DEFAULT_THRESHOLDS["deeply_undervalued"]

    def test_low_beta_adjustment(self) -> None:
        """测试低 β 系数调整（β < 0.8）"""
        calc = SafetyMarginCalculator()
        adjusted = calc._adjust_thresholds(beta=0.5)

        # 低 β 应该缩小阈值
        assert adjusted["deeply_undervalued"] < DEFAULT_THRESHOLDS["deeply_undervalued"]

    def test_normal_beta_no_adjustment(self) -> None:
        """测试正常 β 系数（0.8 ≤ β ≤ 1.5）"""
        calc = SafetyMarginCalculator()
        adjusted = calc._adjust_thresholds(beta=1.0)

        # 正常 β 阈值不变
        assert (
            adjusted["deeply_undervalued"] == DEFAULT_THRESHOLDS["deeply_undervalued"]
        )

    def test_none_beta_no_adjustment(self) -> None:
        """测试 β 为 None 时不调整"""
        calc = SafetyMarginCalculator()
        adjusted = calc._adjust_thresholds(beta=None)

        assert adjusted == DEFAULT_THRESHOLDS


class TestPEPBPercentile:
    """PE/PB 分位辅助判断测试"""

    def test_adjust_by_valuation_percentile_both_low(self) -> None:
        """测试 PE+PB 都在 10% 以下 → 更低估"""
        calc = SafetyMarginCalculator()
        level = calc._adjust_by_valuation_percentile(
            current_level=MarginLevel.UNDERVALUED,
            safety_margin=0.25,
            pe_percentile=5.0,
            pb_percentile=8.0,
            thresholds=DEFAULT_THRESHOLDS,
        )
        # 应该提升一级
        assert level == MarginLevel.DEEPLY_UNDERVALUED

    def test_adjust_by_valuation_percentile_both_high(self) -> None:
        """测试 PE+PB 都在 90% 以上 → 更高估"""
        calc = SafetyMarginCalculator()
        level = calc._adjust_by_valuation_percentile(
            current_level=MarginLevel.OVERVALUED,
            safety_margin=-0.15,
            pe_percentile=95.0,
            pb_percentile=92.0,
            thresholds=DEFAULT_THRESHOLDS,
        )
        # 应该提升一级（更高估）
        assert level == MarginLevel.DEEPLY_OVERVALUED

    def test_adjust_by_valuation_percentile_mixed(self) -> None:
        """测试 PE/PB 分位混合时不调整"""
        calc = SafetyMarginCalculator()
        level = calc._adjust_by_valuation_percentile(
            current_level=MarginLevel.FAIR,
            safety_margin=0.05,
            pe_percentile=30.0,
            pb_percentile=70.0,
            thresholds=DEFAULT_THRESHOLDS,
        )
        # 不应该调整
        assert level == MarginLevel.FAIR


class TestCalcPEPBPercentile:
    """PE/PB 分位计算测试"""

    def test_calc_pe_percentile(self) -> None:
        """测试 PE 历史分位计算"""
        pe_series = pd.Series([10.0, 15.0, 20.0, 25.0, 30.0])
        percentile = SafetyMarginCalculator.calc_pe_percentile(
            pe_series, current_pe=18.0
        )
        # 18.0 < 15.0 和 20.0，所以分位应该是 40%
        assert percentile == pytest.approx(40.0, rel=1.0)

    def test_calc_pb_percentile(self) -> None:
        """测试 PB 历史分位计算"""
        pb_series = pd.Series([1.0, 1.5, 2.0, 2.5, 3.0])
        percentile = SafetyMarginCalculator.calc_pb_percentile(
            pb_series, current_pb=2.5
        )
        # 2.5 < 3.0，所以分位应该是 80%
        assert percentile == pytest.approx(80.0, rel=1.0)

    def test_calc_percentile_empty_series(self) -> None:
        """测试空序列返回默认值 50%"""
        empty_series = pd.Series([], dtype=float)
        percentile = SafetyMarginCalculator.calc_pe_percentile(
            empty_series, current_pe=10.0
        )
        assert percentile == 50.0


class TestCalculateIntegration:
    """calculate 方法集成测试"""

    def test_calculate_complete(self) -> None:
        """测试完整计算流程"""
        calc = SafetyMarginCalculator()
        result = calc.calculate(
            ts_code="600519.SH",
            dcf_value=200.0,
            current_price=100.0,
            beta=1.2,
            pe_percentile=15.0,
            pb_percentile=20.0,
        )

        assert result.ts_code == "600519.SH"
        assert result.dcf_value == 200.0
        assert result.current_price == 100.0
        assert result.safety_margin == pytest.approx(1.0, rel=0.01)
        assert result.level == MarginLevel.DEEPLY_UNDERVALUED
        assert result.beta == 1.2
        assert result.margin_pct == pytest.approx(100.0, rel=1.0)

    def test_calculate_with_eventbus(self) -> None:
        """测试 EventBus 事件发送"""
        with patch("framework.trading.seasons.safety_margin.Events") as mock_events:
            calc = SafetyMarginCalculator()
            calc.calculate(
                ts_code="600519.SH",
                dcf_value=150.0,
                current_price=100.0,
            )

            # 验证事件发送
            mock_events.safety_margin_updated.send.assert_called_once()
