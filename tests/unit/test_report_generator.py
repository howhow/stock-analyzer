"""
报告生成器测试
"""

import pytest

from app.models.analysis import (
    AnalysisResult,
    AnalysisType,
    AnalystReport,
    DimensionScores,
    EntryTiming,
    MTFAlignment,
    Recommendation,
    TraderSignal,
    WyckoffPhase,
)
from app.models.report import ReportFormat
from app.report.generator import ReportGenerator, get_report_generator


class TestReportGenerator:
    """报告生成器测试"""

    @pytest.fixture
    def generator(self) -> ReportGenerator:
        """创建报告生成器"""
        return ReportGenerator()

    @pytest.fixture
    def sample_analysis_result(self) -> AnalysisResult:
        """创建示例分析结果"""
        analyst_report = AnalystReport(
            stock_code="600519.SH",
            stock_name="贵州茅台",
            analysis_type=AnalysisType.LONG,
            fundamental_score=4.2,
            technical_score=3.8,
            dimension_scores=DimensionScores(
                signal_strength=4.0,
                opportunity_quality=3.5,
                risk_level=4.0,
            ),
            total_score=3.8,
            wyckoff_phase=WyckoffPhase.ACCUMULATION,
            support_levels=[1800.0, 1750.0],
            resistance_levels=[1900.0, 1950.0],
        )

        trader_signal = TraderSignal(
            stock_code="600519.SH",
            confidence=75.0,
            mtf_alignment=MTFAlignment.ALIGNED,
            entry_timing=EntryTiming.IMMEDIATE,
            recommendation=Recommendation.BUY,
            expected_return=15.0,
            var_95=5.0,
            max_drawdown=8.0,
            entry_price=1850.0,
            stop_loss_price=1800.0,
            target_price=2100.0,
        )

        return AnalysisResult(
            analysis_id="test_analysis_001",
            stock_code="600519.SH",
            stock_name="贵州茅台",
            analysis_type=AnalysisType.LONG,
            analyst_report=analyst_report,
            trader_signal=trader_signal,
        )

    def test_generator_init(self, generator: ReportGenerator) -> None:
        """测试生成器初始化"""
        assert generator is not None
        assert generator.template_dir is not None
        assert generator.version == "1.0.0"

    def test_generate_html_report(
        self, generator: ReportGenerator, sample_analysis_result: AnalysisResult
    ) -> None:
        """测试生成 HTML 报告"""
        report_content = generator.generate(
            analysis_result=sample_analysis_result,
            format_type=ReportFormat.HTML,
        )

        assert report_content is not None
        assert report_content.report_id is not None
        assert report_content.report_id.startswith("rpt_")
        assert report_content.stock_code == "600519.SH"
        assert report_content.stock_name == "贵州茅台"
        assert report_content.analysis_data is not None

    def test_generate_json_report(
        self, generator: ReportGenerator, sample_analysis_result: AnalysisResult
    ) -> None:
        """测试生成 JSON 报告"""
        report_content = generator.generate(
            analysis_result=sample_analysis_result,
            format_type=ReportFormat.JSON,
        )

        assert report_content is not None
        assert report_content.report_id is not None
        assert report_content.analysis_data is not None

    def test_prepare_report_data(
        self, generator: ReportGenerator, sample_analysis_result: AnalysisResult
    ) -> None:
        """测试准备报告数据"""
        data = generator._prepare_report_data(sample_analysis_result)

        assert data["stock_code"] == "600519.SH"
        assert data["stock_name"] == "贵州茅台"
        assert data["scores"]["total"] == 3.8
        assert data["recommendation"] == "买入"
        assert data["confidence"] == 75.0
        assert data["wyckoff_phase"] == "accumulation"
        assert data["entry_timing"] == "immediate"

    def test_calculate_risk_assessment(self, generator: ReportGenerator) -> None:
        """测试风险评估计算"""
        # 低风险
        assert "低风险" in generator._calculate_risk_assessment(4.5, 3.0, 5.0)

        # 高风险
        assert "高风险" in generator._calculate_risk_assessment(1.5, None, None)

    def test_generate_timing_advice(self, generator: ReportGenerator) -> None:
        """测试时机建议生成"""
        # 立即入场
        advice = generator._generate_timing_advice("immediate", 100.0, 95.0)
        assert "立即入场" in advice
        assert "100.00" in advice
        assert "95.00" in advice

        # 等待
        advice = generator._generate_timing_advice("wait", None, None)
        assert "等待" in advice

    def test_get_score_grade(self, generator: ReportGenerator) -> None:
        """测试评分等级"""
        assert "A+" in generator._get_score_grade(4.8)
        assert "A" in generator._get_score_grade(4.2)
        assert "B" in generator._get_score_grade(3.5)
        assert "C" in generator._get_score_grade(2.5)
        assert "D" in generator._get_score_grade(1.5)

    def test_generate_fallback_html(
        self, generator: ReportGenerator, sample_analysis_result: AnalysisResult
    ) -> None:
        """测试后备 HTML 生成"""
        data = generator._prepare_report_data(sample_analysis_result)
        html = generator._generate_fallback_html(data)

        assert "<!DOCTYPE html>" in html
        assert "600519.SH" in html
        assert "贵州茅台" in html
        assert "买入" in html

    def test_get_report_generator(self) -> None:
        """测试获取全局生成器"""
        gen1 = get_report_generator()
        gen2 = get_report_generator()

        assert gen1 is gen2
