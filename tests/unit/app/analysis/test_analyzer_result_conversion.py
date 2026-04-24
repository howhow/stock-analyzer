"""
AnalysisResult转换测试

测试AnalyzerResult到AnalysisResult的转换
"""

from app.analysis.base import AnalyzerResult
from app.models.analysis import AnalysisType


class TestAnalyzerResultConversion:
    """测试AnalyzerResult转换"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = AnalyzerResult("test_analyzer")
        result.add_score("fundamental", 85.0)
        result.add_score("technical", 90.0)
        result.add_signal("test_signal")

        data = result.to_dict()

        assert data["analyzer"] == "test_analyzer"
        assert data["scores"]["fundamental"] == 85.0
        assert data["scores"]["technical"] == 90.0
        assert "test_signal" in data["signals"]

    def test_to_analysis_result(self):
        """测试转换为API响应模型"""
        result = AnalyzerResult("analyst")
        result.add_score("fundamental", 80.0)
        result.add_score("technical", 70.0)
        result.add_score("total", 75.0)
        result.add_signal("上涨趋势")
        result.add_warning("测试警告")

        analysis_result = result.to_analysis_result(
            stock_code="600276.SH",
            stock_name="恒瑞医药",
            analysis_type="both",
        )

        assert analysis_result.stock_code == "600276.SH"
        assert analysis_result.stock_name == "恒瑞医药"
        assert analysis_result.analysis_type == AnalysisType.BOTH
        assert analysis_result.analyst_report is not None
        assert analysis_result.trader_signal is not None
        assert analysis_result.analyst_report.fundamental_score == 4.0  # 80/20
        assert analysis_result.analyst_report.technical_score == 3.5  # 70/20
