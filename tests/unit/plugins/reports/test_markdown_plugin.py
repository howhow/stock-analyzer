"""MarkdownReportPlugin 测试

覆盖报告生成核心 — 用户直接看到的输出，必须 100% 覆盖。
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plugins.reports.markdown.plugin import MarkdownReportPlugin


class TestMarkdownReportPlugin:
    """测试 Markdown 报告插件"""

    @pytest.fixture
    def plugin(self):
        """创建插件实例"""
        return MarkdownReportPlugin(template_dir="./templates/reports")

    @pytest.fixture
    def sample_data(self):
        """示例分析结果数据"""
        return {
            "stock_code": "600519.SH",
            "stock_name": "贵州茅台",
            "report_date": "2024-01-01",
            "data_source": "Stock Analyzer",
            "summary": "测试摘要内容",
            "scores": {
                "technical": 85,
                "fundamental": 90,
                "risk": 75,
            },
            "recommendation": {
                "action": "BUY",
                "confidence": 0.85,
                "reason": "测试建议理由",
            },
            "technical_analysis": {
                "indicators": {
                    "MACD": "金叉",
                    "RSI": 65,
                },
            },
            "risks": ["市场风险", "政策风险"],
            "opportunities": ["增长机会", "估值修复"],
            "trading_advice": {
                "entry_price": 100.0,
                "stop_loss": 95.0,
                "target_price": 120.0,
            },
        }

    # === 属性测试 ===

    def test_name_property(self, plugin):
        """名称属性"""
        assert plugin.name == "markdown"

    def test_file_extension_property(self, plugin):
        """文件扩展名属性"""
        assert plugin.file_extension == ".md"

    def test_content_type_property(self, plugin):
        """MIME 类型属性"""
        assert plugin.content_type == "text/markdown"

    # === generate 测试 ===

    def test_generate_with_dict(self, plugin, sample_data):
        """使用 dict 数据生成报告"""
        result = plugin.generate(sample_data)

        assert isinstance(result, str)
        assert "600519.SH" in result
        assert "贵州茅台" in result
        assert "测试摘要内容" in result
        assert "BUY" in result

    def test_generate_with_pydantic_model(self, plugin):
        """使用 Pydantic model 生成报告"""
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
        }

        result = plugin.generate(mock_model)

        assert "000001.SZ" in result
        assert "平安银行" in result

    def test_generate_with_old_pydantic(self, plugin):
        """使用旧版 Pydantic (dict 方法)"""
        mock_model = MagicMock()
        # 没有 model_dump，只有 dict
        del mock_model.model_dump
        mock_model.dict.return_value = {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
        }

        result = plugin.generate(mock_model)

        assert "000001.SZ" in result

    def test_generate_with_string_input(self, plugin):
        """字符串输入处理"""
        result = plugin.generate("raw string input")

        assert isinstance(result, str)
        # 字符串输入会被包装为 {"raw_result": "raw string input"}
        # 最终报告中不会直接显示原始字符串，而是显示为未知代码的报告

    def test_generate_empty_data(self, plugin):
        """空数据生成报告"""
        result = plugin.generate({})

        assert isinstance(result, str)
        assert "未知" in result  # 默认股票代码

    def test_generate_missing_optional_fields(self, plugin):
        """缺少可选字段"""
        minimal_data = {
            "stock_code": "600519.SH",
        }

        result = plugin.generate(minimal_data)

        assert "600519.SH" in result

    # === render_to_file 测试 ===

    def test_render_to_file(self, plugin, sample_data):
        """渲染到文件"""
        output_path = "local_test_report/test_markdown_report"

        result_path = plugin.render_to_file(sample_data, output_path)

        assert result_path.endswith(".md")
        assert Path(result_path).exists()
        content = Path(result_path).read_text(encoding="utf-8")
        assert "600519.SH" in content

    def test_render_to_file_with_extension(self, plugin, sample_data):
        """输出路径已有扩展名"""
        output_path = "local_test_report/test_report.txt"

        result_path = plugin.render_to_file(sample_data, output_path)

        # 应该替换为 .md
        assert result_path.endswith(".md")
        assert not result_path.endswith(".txt")

    def test_render_to_file_creates_directory(self, plugin, sample_data):
        """自动创建目录"""
        output_path = "local_test_report/sub/dir/report"

        result_path = plugin.render_to_file(sample_data, output_path)

        assert Path(result_path).exists()

    # === _extract_data 测试 ===

    def test_extract_data_from_dict(self, plugin):
        """从 dict 提取"""
        data = {"key": "value"}
        result = plugin._extract_data(data)
        assert result == data

    def test_extract_data_from_pydantic(self, plugin):
        """从 Pydantic model 提取"""
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"key": "value"}

        result = plugin._extract_data(mock_model)
        assert result == {"key": "value"}

    # === 各部分生成测试 ===

    def test_generate_header(self, plugin):
        """报告头部"""
        data = {
            "stock_code": "600519.SH",
            "stock_name": "贵州茅台",
            "report_date": "2024-01-01",
            "data_source": "Test Source",
        }
        header = plugin._generate_header(data)

        assert "600519.SH" in header
        assert "贵州茅台" in header
        assert "2024-01-01" in header
        assert "Test Source" in header

    def test_generate_header_without_name(self, plugin):
        """无股票名称"""
        data = {"stock_code": "600519.SH"}
        header = plugin._generate_header(data)

        assert "600519.SH" in header
        # 没有名称时标题只有股票代码
        assert "贵州茅台" not in header

    def test_generate_summary(self, plugin):
        """摘要部分"""
        data = {"summary": "测试摘要"}
        result = plugin._generate_summary(data)

        assert "测试摘要" in result
        assert "分析摘要" in result

    def test_generate_summary_empty(self, plugin):
        """空摘要不生成"""
        data = {}
        result = plugin._generate_summary(data)
        assert result == ""

    def test_generate_scores(self, plugin):
        """评分部分"""
        data = {"scores": {"technical": 85}}
        result = plugin._generate_scores(data)

        assert "technical" in result
        assert "85" in result

    def test_generate_scores_empty(self, plugin):
        """空评分"""
        data = {}
        result = plugin._generate_scores(data)
        assert result == ""

    def test_generate_recommendation(self, plugin):
        """建议部分"""
        data = {
            "recommendation": {
                "action": "BUY",
                "confidence": 0.85,
                "reason": "测试",
            }
        }
        result = plugin._generate_recommendation(data)

        assert "BUY" in result
        assert "测试" in result

    def test_generate_recommendation_sell(self, plugin):
        """SELL 建议"""
        data = {
            "recommendation": {
                "action": "SELL",
                "confidence": 0.9,
            }
        }
        result = plugin._generate_recommendation(data)
        assert "🔴" in result
        assert "SELL" in result

    def test_generate_recommendation_hold(self, plugin):
        """HOLD 建议"""
        data = {
            "recommendation": {
                "action": "HOLD",
                "confidence": 0.5,
            }
        }
        result = plugin._generate_recommendation(data)
        assert "🟡" in result
        assert "HOLD" in result

    def test_generate_recommendation_unknown(self, plugin):
        """未知建议类型"""
        data = {
            "recommendation": {
                "action": "UNKNOWN",
                "confidence": 0.5,
            }
        }
        result = plugin._generate_recommendation(data)
        assert "⚪" in result

    def test_generate_technical_analysis(self, plugin):
        """技术分析部分"""
        data = {"technical_analysis": {"indicators": {"MACD": "金叉", "RSI": 65}}}
        result = plugin._generate_technical_analysis(data)

        assert "MACD" in result
        assert "金叉" in result
        assert "RSI" in result

    def test_generate_risks(self, plugin):
        """风险提示"""
        data = {"risks": ["风险1", "风险2"]}
        result = plugin._generate_risks(data)

        assert "风险1" in result
        assert "风险2" in result

    def test_generate_opportunities(self, plugin):
        """机会分析"""
        data = {"opportunities": ["机会1"]}
        result = plugin._generate_opportunities(data)

        assert "机会1" in result

    def test_generate_trading_advice(self, plugin):
        """交易建议"""
        data = {
            "trading_advice": {
                "entry_price": 100.0,
                "stop_loss": 95.0,
                "target_price": 120.0,
            }
        }
        result = plugin._generate_trading_advice(data)

        assert "100.0" in result
        assert "95.0" in result
        assert "120.0" in result

    def test_generate_trading_advice_partial(self, plugin):
        """部分交易建议"""
        data = {"trading_advice": {"entry_price": 100.0}}
        result = plugin._generate_trading_advice(data)

        assert "100.0" in result
        assert "止损" not in result  # 没有 stop_loss

    def test_generate_footer(self, plugin):
        """报告尾部"""
        footer = plugin._generate_footer({})

        assert "仅供参考" in footer
        assert "Stock Analyzer" in footer

    # === 边界测试 ===

    def test_generate_with_none_values(self, plugin):
        """None 值处理"""
        data = {
            "stock_code": None,
            "summary": None,
            "scores": None,
        }
        result = plugin.generate(data)

        assert isinstance(result, str)

    def test_generate_large_scores(self, plugin):
        """大分数值"""
        data = {"scores": {"metric": 150}}  # 超过 100
        result = plugin._generate_scores(data)

        assert "150" in result
        # 进度条应该满格
        assert "██████████" in result
