"""测试分析结果模型"""

from datetime import datetime

import pytest

from framework.models.analysis import AnalysisResult


class TestAnalysisResult:
    """测试 AnalysisResult 模型"""

    def test_create_with_required_fields(self):
        """测试创建 - 仅必填字段"""
        result = AnalysisResult(
            analysis_id="test-001",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.5,
            signal="buy",
            signal_strength=3.5,
            confidence=80.0,
        )

        assert result.analysis_id == "test-001"
        assert result.stock_code == "600519.SH"
        assert result.analysis_type == "short"
        assert result.total_score == 75.5
        assert result.signal == "buy"
        assert result.signal_strength == 3.5
        assert result.confidence == 80.0

    def test_create_with_all_fields(self):
        """测试创建 - 所有字段"""
        result = AnalysisResult(
            analysis_id="test-002",
            stock_code="600519.SH",
            stock_name="贵州茅台",
            analysis_type="both",
            total_score=85.0,
            fundamental_score=80.0,
            technical_score=90.0,
            sentiment_score=75.0,
            signal="buy",
            signal_strength=4.0,
            confidence=85.0,
            details={"pe_ratio": 25.5, "pb_ratio": 8.2},
            indicators={"rsi": 65.0, "macd": {"macd": 1.5, "signal": 1.2}},
            recommendations=["建议买入", "关注技术面突破"],
            warnings=["短期涨幅较大"],
            data_source="tushare",
            ai_provider="openai",
            processing_time_ms=1500.0,
        )

        assert result.stock_name == "贵州茅台"
        assert result.fundamental_score == 80.0
        assert result.technical_score == 90.0
        assert result.sentiment_score == 75.0
        assert "pe_ratio" in result.details
        assert len(result.recommendations) == 2
        assert len(result.warnings) == 1

    def test_get_risk_level_low(self):
        """测试风险等级 - 低风险"""
        result = AnalysisResult(
            analysis_id="test-003",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.0,
            signal="buy",
            signal_strength=3.0,
            confidence=80.0,
        )

        assert result.get_risk_level() == "low"

    def test_get_risk_level_medium(self):
        """测试风险等级 - 中风险"""
        result = AnalysisResult(
            analysis_id="test-004",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=50.0,
            signal="hold",
            signal_strength=2.0,
            confidence=60.0,
        )

        assert result.get_risk_level() == "medium"

    def test_get_risk_level_high(self):
        """测试风险等级 - 高风险"""
        result = AnalysisResult(
            analysis_id="test-005",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=30.0,
            signal="sell",
            signal_strength=2.0,
            confidence=70.0,
        )

        assert result.get_risk_level() == "high"

    def test_is_reliable_true(self):
        """测试可靠性 - 可靠"""
        result = AnalysisResult(
            analysis_id="test-006",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.0,
            signal="buy",
            signal_strength=3.0,
            confidence=80.0,
        )

        assert result.is_reliable() is True

    def test_is_reliable_false(self):
        """测试可靠性 - 不可靠"""
        result = AnalysisResult(
            analysis_id="test-007",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.0,
            signal="buy",
            signal_strength=3.0,
            confidence=40.0,
        )

        assert result.is_reliable() is False

    def test_to_summary(self):
        """测试生成摘要"""
        result = AnalysisResult(
            analysis_id="test-008",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.0,
            signal="buy",
            signal_strength=3.0,
            confidence=80.0,
        )

        summary = result.to_summary()

        assert "600519.SH" in summary
        assert "综合评分" in summary
        assert "买入" in summary
        assert "低风险" in summary

    def test_default_values(self):
        """测试默认值"""
        result = AnalysisResult(
            analysis_id="test-009",
            stock_code="600519.SH",
            analysis_type="short",
            total_score=75.0,
            signal="hold",
            signal_strength=2.0,
            confidence=50.0,
        )

        assert result.details == {}
        assert result.indicators == {}
        assert result.recommendations == []
        assert result.warnings == []
        assert result.stock_name is None
        assert result.fundamental_score is None
        assert result.data_source is None
