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

    # ========== 新增测试：覆盖 DCF/安全边际/四季/五行分支 ==========

    def test_generate_fundamental_analysis_with_dcf(self, generator):
        """测试基本面分析 - 带DCF估值"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "dcf": {
                "dcf_mean": 25.5,
                "valuation": "低估",
            }
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "DCF估值" in fund
        assert "25.50" in fund
        assert "低估" in fund

    def test_generate_fundamental_analysis_with_safety_margin(self, generator):
        """测试基本面分析 - 带安全边际"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "safety_margin": {
                "current_price": 20.0,
                "dcf_value": 25.5,
                "margin_percent": 27.5,
                "rating": "强烈买入",
            }
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "安全边际" in fund
        assert "20.00" in fund
        assert "27.5%" in fund
        assert "强烈买入" in fund

    def test_generate_fundamental_analysis_with_seasons(self, generator):
        """测试基本面分析 - 带四季引擎"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "seasons": {
                "current_season": "春季",
                "confidence": 0.85,
            }
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "四季分析" in fund
        assert "春季" in fund
        assert "0.85" in fund

    def test_generate_fundamental_analysis_with_wuxing(self, generator):
        """测试基本面分析 - 带五行引擎"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "wuxing": {
                "element": "火",
                "confidence": 0.75,
                "action": "买入",
            }
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "五行分析" in fund
        assert "火" in fund
        assert "买入" in fund

    def test_generate_fundamental_analysis_with_fundamentals(self, generator):
        """测试基本面分析 - 带财务指标"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            fundamentals={
                "pe_ttm": 15.5,
                "pb": 1.2,
                "roe": 0.18,
                "report_date": "2024-03-31",
            },
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "财务指标" in fund
        assert "15.50" in fund
        assert "1.20" in fund
        assert "report_date" not in fund  # 应该被过滤掉

    def test_generate_fundamental_analysis_fallback_analyst(self, generator):
        """测试基本面分析 - 从analyst回退"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "analyst": {
                "scores": {
                    "fundamental": 82.5,
                }
            }
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "基本面评分" in fund
        assert "82.5" in fund

    def test_generate_fundamental_analysis_no_data(self, generator):
        """测试基本面分析 - 无数据"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        fund = generator._generate_fundamental_analysis(data)
        assert "暂无详细基本面数据" in fund

    def test_generate_technical_analysis_with_trend(self, generator):
        """测试技术分析 - 带趋势"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {}
        result.signals = ["上涨趋势确认", "RSI中性"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        tech = generator._generate_technical_analysis(data)
        assert "上涨" in tech

    def test_generate_technical_analysis_with_downtrend(self, generator):
        """测试技术分析 - 下跌趋势"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {}
        result.signals = ["下跌趋势确认"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        tech = generator._generate_technical_analysis(data)
        assert "下跌" in tech

    def test_generate_key_indicators_with_quotes(self, generator):
        """测试关键指标 - 带行情数据"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
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
            ),
        ]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            quotes=quotes,
        )

        indicators = generator._generate_key_indicators(data)
        assert "最新价" in indicators
        assert "10.50" in indicators

    def test_generate_key_indicators_no_quotes(self, generator):
        """测试关键指标 - 无行情数据"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        indicators = generator._generate_key_indicators(data)
        assert indicators is not None
        assert "## 关键指标" in indicators

    def test_generate_opportunities_with_signals(self, generator):
        """测试机会 - 带买入信号"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.signals = ["买入信号", "上涨趋势", "突破阻力位"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        opps = generator._generate_opportunities(data)
        assert "买入信号" in opps

    def test_generate_opportunities_empty(self, generator):
        """测试机会 - 无信号"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.signals = ["RSI中性"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        opps = generator._generate_opportunities(data)
        assert "暂无明确投资机会" in opps

    def test_generate_risks_with_warnings(self, generator):
        """测试风险 - 带警告"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.warnings = ["高风险", "波动率异常"]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        risks = generator._generate_risks(data)
        assert "高风险" in risks
        assert "波动率异常" in risks

    def test_generate_risks_empty(self, generator):
        """测试风险 - 无警告"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.warnings = []

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        risks = generator._generate_risks(data)
        assert "暂无明确风险提示" in risks

    def test_generate_trading_advice_with_details(self, generator):
        """测试交易建议 - 显示操作方向和置信度"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {
            "recommendation": "买入",
            "confidence": 85.0,
        }

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        advice = generator._generate_trading_advice(data)
        assert "买入" in advice
        assert "85.0%" in advice

    def test_generate_recommendation_map(self, generator):
        """测试建议映射"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
        result.details = {"recommendation": "强烈买入", "confidence": 95.0}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        rec = generator._generate_recommendation(data)
        assert "强烈买入" in rec
        assert "95" in rec

    def test_generate_with_quotes_data(self, generator):
        """测试带行情数据生成完整报告"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}
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
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 2),
                open=10.5,
                high=11.5,
                low=10.0,
                close=11.0,
                volume=1200000,
                amount=13200000.0,
            ),
        ]

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            quotes=quotes,
        )

        md = generator.generate(data)
        assert "行情数据" in md or "K线" in md or "平安银行" in md

    def test_generate_metadata_with_version(self, generator):
        """测试元数据 - 基础功能"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 85.0}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )
        # ReportData 没有 version 字段，测试基础功能
        meta = generator._generate_metadata(data)
        assert "平安银行" in meta or "000001.SZ" in meta

    def test_empty_signals_and_warnings(self, generator):
        """测试空信号和警告"""
        result = AnalyzerResult("StockAnalyzer")
        result.scores = {"total": 75.0}
        result.signals = []
        result.warnings = []
        result.details = {}

        data = ReportData.from_analysis(
            result=result,
            stock_code="000001.SZ",
            stock_name="平安银行",
        )

        md = generator.generate(data)
        assert md is not None
        assert "暂无明确投资机会" in md or "暂无明确风险提示" in md
