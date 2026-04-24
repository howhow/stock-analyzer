"""测试报告接口协议"""

import pytest


class MockReport:
    """模拟报告实现"""

    @property
    def name(self) -> str:
        return "markdown"

    @property
    def file_extension(self) -> str:
        return ".md"

    @property
    def content_type(self) -> str:
        return "text/markdown"

    def generate(self, analysis_result, template: str | None = None, **kwargs) -> str:
        return "# Mock Report"

    def render_to_file(
        self, analysis_result, output_path: str, template: str | None = None, **kwargs
    ) -> str:
        return output_path


class TestReportInterface:
    """测试报告接口"""

    def test_mock_implementation_satisfies_interface(self):
        """验证模拟实现满足接口"""
        mock = MockReport()

        assert mock.name == "markdown"
        assert mock.file_extension == ".md"

    def test_generate_returns_string(self):
        """验证 generate 返回字符串"""
        mock = MockReport()
        result = mock.generate(None)

        assert isinstance(result, str)
        assert "# Mock Report" in result
