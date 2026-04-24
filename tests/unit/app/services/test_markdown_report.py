"""
Markdown 报告生成器完整测试
"""

from datetime import date

import pytest

from app.analysis.base import AnalyzerResult
from app.models.stock import DailyQuote
from app.report.markdown_report import MarkdownReportGenerator
from app.report.report_data import ReportData


class TestMarkdownReportGeneratorComplete:
    """Markdown 报告生成器完整测试"""

    @pytest.fixture
    def generator(self):
        """创建生成器"""
        return MarkdownReportGenerator()

    @pytest.fixture
    def sample_data(self):
        """示例报告数据"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {
            "total": 85.5,
            "fundamental": 80.0,
            "technical": 90.0,
        }
        result.details = {
            "stock_name": "平安银行",
            "analysis_type": "full",
            "analysis_days": 120,
            "analyst": {
                "scores": {
                    "fundamental": 80.0,
                    "technical": 90.0,
                }
            },
            "trader": {
                "recommendation": "买入",
                "confidence": 85.0,
            },
        }
        result.signals = ["上涨趋势", "RSI中性"]
        result.warnings = ["注意风险"]

        return ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

    def test_generate_complete_report(self, generator, sample_data):
        """测试生成完整报告"""
        md = generator.generate(sample_data)

        assert md is not None
        assert isinstance(md, str)
        assert "# 股票分析报告" in md
        assert "平安银行" in md

    def test_generate_with_quotes(self, generator):
        """测试带行情数据"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.details = {}

        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                high=11.0,
                low=9.5,
                close=10.5,
                volume=1000000,
                amount=10500000.0,
            )
        ]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            quotes=quotes,
        )

        md = generator.generate(data)
        assert md is not None
        assert "平安银行" in md

    def test_generate_header(self, generator, sample_data):
        """测试生成标题"""
        header = generator._generate_header(sample_data)

        assert header is not None
        assert "# 股票分析报告" in header
        assert "平安银行" in header

    def test_generate_basic_info(self, generator, sample_data):
        """测试生成基本信息"""
        info = generator._generate_basic_info(sample_data)

        assert info is not None
        assert "## 基本信息" in info
        assert "平安银行" in info

    def test_generate_scores(self, generator, sample_data):
        """测试生成评分"""
        scores = generator._generate_scores(sample_data)

        assert scores is not None
        assert "## 评分结果" in scores
        assert "85.5" in scores

    def test_generate_recommendation(self, generator, sample_data):
        """测试生成建议"""
        rec = generator._generate_recommendation(sample_data)

        assert rec is not None
        assert "##" in rec  # 返回标题

    def test_generate_key_indicators(self, generator, sample_data):
        """测试生成关键指标"""
        indicators = generator._generate_key_indicators(sample_data)

        assert indicators is not None

    def test_generate_technical_analysis(self, generator, sample_data):
        """测试生成技术分析"""
        tech = generator._generate_technical_analysis(sample_data)

        assert tech is not None

    def test_generate_fundamental_analysis(self, generator, sample_data):
        """测试生成基本面分析"""
        fund = generator._generate_fundamental_analysis(sample_data)

        assert fund is not None

    def test_generate_risks(self, generator, sample_data):
        """测试生成风险"""
        risks = generator._generate_risks(sample_data)

        assert risks is not None

    def test_generate_opportunities(self, generator, sample_data):
        """测试生成机会"""
        opps = generator._generate_opportunities(sample_data)

        assert opps is not None

    def test_generate_trading_advice(self, generator, sample_data):
        """测试生成交易建议"""
        advice = generator._generate_trading_advice(sample_data)

        assert advice is not None

    def test_generate_metadata(self, generator, sample_data):
        """测试生成元数据"""
        meta = generator._generate_metadata(sample_data)

        assert meta is not None

    def test_empty_result(self, generator):
        """测试空结果"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {}
        result.details = {}
        result.signals = []
        result.warnings = []

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        md = generator.generate(data)
        assert md is not None

    def test_analysis_type_technical(self, generator):
        """测试技术分析类型"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.details = {"analysis_type": "technical"}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            analysis_type="technical",
        )

        md = generator.generate(data)
        assert md is not None

    def test_analysis_type_fundamental(self, generator):
        """测试基本面分析类型"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.details = {"analysis_type": "fundamental"}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            analysis_type="fundamental",
        )

        md = generator.generate(data)
        assert md is not None

    def test_with_warnings(self, generator):
        """测试带警告"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.details = {}
        result.warnings = ["高风险警告", "注意市场波动"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        md = generator.generate(data)
        assert md is not None

    def test_with_signals(self, generator):
        """测试带信号"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.details = {}
        result.signals = ["买入信号", "上涨趋势", "RSI超买"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        md = generator.generate(data)
        assert md is not None
