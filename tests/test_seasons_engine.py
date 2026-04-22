"""四季引擎单元测试

测试目标:
- 季节判断逻辑
- 置信度计算
- EventBus 集成
"""

from unittest.mock import MagicMock, patch

import pytest

from framework.trading.seasons.engine import Season, SeasonsEngine, SeasonState
from framework.trading.seasons.safety_margin import MarginLevel, SafetyMarginCalculator


class TestSeason:
    """Season 枚举测试"""

    def test_season_values(self) -> None:
        """测试季节枚举值"""
        assert Season.SPRING.value == "spring"
        assert Season.SUMMER.value == "summer"
        assert Season.AUTUMN.value == "autumn"
        assert Season.WINTER.value == "winter"


class TestSeasonState:
    """SeasonState 数据模型测试"""

    def test_position_guidance_spring(self) -> None:
        """测试春季仓位指导"""
        mock_result = MagicMock()
        mock_result.safety_margin = 0.30
        mock_result.level = MarginLevel.UNDERVALUED

        state = SeasonState(
            ts_code="600519.SH",
            season=Season.SPRING,
            confidence=0.85,
            safety_margin_result=mock_result,
        )
        assert state.position_guidance == "建仓 50-70%"

    def test_position_guidance_winter(self) -> None:
        """测试冬季仓位指导"""
        mock_result = MagicMock()
        mock_result.safety_margin = -0.25
        mock_result.level = MarginLevel.DEEPLY_OVERVALUED

        state = SeasonState(
            ts_code="600519.SH",
            season=Season.WINTER,
            confidence=0.90,
            safety_margin_result=mock_result,
        )
        assert state.position_guidance == "清仓"


class TestSeasonsEngine:
    """SeasonsEngine 核心功能测试"""

    def test_initialization(self) -> None:
        """测试初始化"""
        engine = SeasonsEngine()
        assert engine._calculator is not None

    def test_analyze_deeply_undervalued_to_spring(self) -> None:
        """测试极度低估 → 春季"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=200.0,
            current_price=100.0,  # 安全边际 100%
        )

        assert state.season == Season.SPRING
        assert state.ts_code == "600519.SH"

    def test_analyze_fair_to_summer(self) -> None:
        """测试合理估值 → 夏季"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=105.0,
            current_price=100.0,  # 安全边际 5%
        )

        assert state.season == Season.SUMMER

    def test_analyze_overvalued_to_autumn(self) -> None:
        """测试高估 → 秋季"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=85.0,
            current_price=100.0,  # 安全边际 -15%
        )

        assert state.season == Season.AUTUMN

    def test_analyze_deeply_overvalued_to_winter(self) -> None:
        """测试极度高估 → 冬季"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=70.0,
            current_price=100.0,  # 安全边际 -30%
        )

        assert state.season == Season.WINTER

    def test_analyze_with_beta(self) -> None:
        """测试 β 系数影响季节判断"""
        engine = SeasonsEngine()

        # 高 β → 放大阈值，同样的安全边际可能被判断为不同等级
        state_high_beta = engine.analyze(
            ts_code="600519.SH",
            dcf_value=150.0,
            current_price=100.0,
            beta=2.0,  # 高波动
        )

        # 低 β → 缩小阈值
        state_low_beta = engine.analyze(
            ts_code="600276.SH",
            dcf_value=150.0,
            current_price=100.0,
            beta=0.5,  # 低波动
        )

        # 两者都是春季，但高 β 需要更大安全边际才能达到极度低估
        assert state_high_beta.season == Season.SPRING
        assert state_low_beta.season == Season.SPRING


class TestConfidenceCalculation:
    """置信度计算测试"""

    def test_confidence_high_margin(self) -> None:
        """测试大安全边际 → 高置信度"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=200.0,
            current_price=100.0,  # 安全边际 100%
        )

        assert state.confidence >= 0.95

    def test_confidence_low_margin(self) -> None:
        """测试小安全边际 → 低置信度"""
        engine = SeasonsEngine()
        state = engine.analyze(
            ts_code="600519.SH",
            dcf_value=105.0,
            current_price=100.0,  # 安全边际 5%
        )

        assert 0.5 <= state.confidence <= 0.7

    def test_confidence_boost_with_beta(self) -> None:
        """测试有 β 数据 → 置信度提升"""
        engine = SeasonsEngine()

        state_with_beta = engine.analyze(
            ts_code="600519.SH",
            dcf_value=120.0,
            current_price=100.0,
            beta=1.2,
        )

        state_without_beta = engine.analyze(
            ts_code="600276.SH",
            dcf_value=120.0,
            current_price=100.0,
            beta=None,
        )

        # 有 β 的置信度应该更高
        assert state_with_beta.confidence > state_without_beta.confidence


class TestSeasonChangeEvent:
    """季节变化事件测试"""

    def test_season_changed_event_sent(self) -> None:
        """测试季节变化时发送事件"""
        with patch("framework.trading.seasons.engine.Events") as mock_events:
            engine = SeasonsEngine()

            # 第一次分析：春季
            engine.analyze(
                ts_code="600519.SH",
                dcf_value=200.0,
                current_price=100.0,
            )
            # 第一次没有上一季节，不发送事件
            mock_events.season_changed.send.assert_not_called()

            # 第二次分析：高估 → 秋季
            engine.analyze(
                ts_code="600519.SH",
                dcf_value=85.0,
                current_price=100.0,
            )

            # 季节变化：春季 → 秋季，应该发送事件
            mock_events.season_changed.send.assert_called_once()
            call_kwargs = mock_events.season_changed.send.call_args.kwargs
            assert call_kwargs["ts_code"] == "600519.SH"
            assert call_kwargs["old_season"] == "spring"
            assert call_kwargs["new_season"] == "autumn"


class TestGetCurrentState:
    """获取当前状态测试"""

    def test_get_current_state_exists(self) -> None:
        """测试获取已存在的状态"""
        engine = SeasonsEngine()
        engine.analyze(
            ts_code="600519.SH",
            dcf_value=200.0,
            current_price=100.0,
        )

        state = engine.get_current_state("600519.SH")
        assert state is not None
        assert state.ts_code == "600519.SH"

    def test_get_current_state_not_exists(self) -> None:
        """测试获取不存在的状态"""
        engine = SeasonsEngine()
        state = engine.get_current_state("000001.SZ")
        assert state is None
