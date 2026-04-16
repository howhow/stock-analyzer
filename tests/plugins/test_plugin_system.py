"""
Week 4 插件系统测试

测试插件管理器和所有插件。
"""

import pytest

from framework.interfaces.ai_provider import AIProviderInterface
from framework.interfaces.report import ReportInterface


# ============================================================
# Plugin Manager Tests
# ============================================================


class TestPluginManager:
    """插件管理器测试"""

    def test_import_plugin_manager(self):
        """测试导入插件管理器"""
        from framework.core.plugin_manager import PluginManager

        assert PluginManager is not None

    def test_plugin_manager_initialization(self):
        """测试插件管理器初始化"""
        from framework.core.plugin_manager import PluginManager

        manager = PluginManager()
        assert manager is not None

    def test_discover_plugins(self):
        """测试插件发现"""
        from framework.core.plugin_manager import PluginManager

        manager = PluginManager()
        discovered = manager.discover_plugins("plugins")
        assert len(discovered) >= 4  # 至少 4 个插件


# ============================================================
# AI Provider Plugin Tests
# ============================================================


class TestAIProviderPlugins:
    """AI 提供商插件测试"""

    def test_import_openai_plugin(self):
        """测试导入 OpenAI 插件"""
        from plugins.ai_providers.openai import OpenAIPlugin

        assert OpenAIPlugin is not None

    def test_import_anthropic_plugin(self):
        """测试导入 Anthropic 插件"""
        from plugins.ai_providers.anthropic import AnthropicPlugin

        assert AnthropicPlugin is not None

    def test_openai_implements_interface(self):
        """测试 OpenAI 插件实现接口"""
        from plugins.ai_providers.openai import OpenAIPlugin

        plugin = OpenAIPlugin(api_key="test_key")
        assert isinstance(plugin, AIProviderInterface)
        assert plugin.name == "openai"
        assert len(plugin.supported_models) > 0

    def test_anthropic_implements_interface(self):
        """测试 Anthropic 插件实现接口"""
        from plugins.ai_providers.anthropic import AnthropicPlugin

        plugin = AnthropicPlugin(api_key="test_key")
        assert isinstance(plugin, AIProviderInterface)
        assert plugin.name == "anthropic"
        assert len(plugin.supported_models) > 0


# ============================================================
# Report Plugin Tests
# ============================================================


class TestReportPlugins:
    """报告插件测试"""

    def test_import_markdown_plugin(self):
        """测试导入 Markdown 插件"""
        from plugins.reports.markdown import MarkdownReportPlugin

        assert MarkdownReportPlugin is not None

    def test_import_pdf_plugin(self):
        """测试导入 PDF 插件"""
        from plugins.reports.pdf import PDFReportPlugin

        assert PDFReportPlugin is not None

    def test_markdown_implements_interface(self):
        """测试 Markdown 插件实现接口"""
        from plugins.reports.markdown import MarkdownReportPlugin

        plugin = MarkdownReportPlugin()
        assert isinstance(plugin, ReportInterface)
        assert plugin.name == "markdown"
        assert plugin.file_extension == ".md"
        assert plugin.content_type == "text/markdown"

    def test_pdf_implements_interface(self):
        """测试 PDF 插件实现接口"""
        from plugins.reports.pdf import PDFReportPlugin

        plugin = PDFReportPlugin()
        assert isinstance(plugin, ReportInterface)
        assert plugin.name == "pdf"
        assert plugin.file_extension == ".pdf"
        assert plugin.content_type == "application/pdf"

    def test_markdown_generate(self):
        """测试 Markdown 报告生成"""
        from plugins.reports.markdown import MarkdownReportPlugin

        plugin = MarkdownReportPlugin()
        test_data = {
            "stock_code": "600519.SH",
            "stock_name": "贵州茅台",
            "summary": "测试摘要",
            "scores": {"技术面": 75, "基本面": 85},
            "recommendation": {
                "action": "HOLD",
                "confidence": 0.65,
                "reason": "测试原因",
            },
        }

        content = plugin.generate(test_data)
        assert "600519.SH" in content
        assert "贵州茅台" in content
        assert "测试摘要" in content
        assert "HOLD" in content

    def test_markdown_render_to_file(self, tmp_path):
        """测试 Markdown 渲染到文件"""
        from plugins.reports.markdown import MarkdownReportPlugin

        plugin = MarkdownReportPlugin()
        test_data = {"stock_code": "000001.SZ"}

        output_path = plugin.render_to_file(
            test_data,
            str(tmp_path / "test_report"),
        )

        assert output_path.endswith(".md")
        content = open(output_path).read()
        assert "000001.SZ" in content


# ============================================================
# Integration Tests
# ============================================================


class TestPluginIntegration:
    """插件集成测试"""

    def test_plugin_manager_register(self):
        """测试插件注册"""
        from framework.core.plugin_manager import PluginManager
        from plugins.reports.markdown import MarkdownReportPlugin

        manager = PluginManager()
        plugin = MarkdownReportPlugin()
        manager.register_plugin(plugin, "report", "markdown")

        assert "markdown" in manager.list_plugins("report")

    def test_plugin_manager_get_plugin(self):
        """测试获取插件"""
        from framework.core.plugin_manager import PluginManager
        from plugins.reports.markdown import MarkdownReportPlugin

        manager = PluginManager()
        plugin = MarkdownReportPlugin()
        manager.register_plugin(plugin, "report", "markdown")

        retrieved = manager.get_plugin("markdown", "report")
        assert retrieved is plugin

    def test_load_plugin_from_entrypoint(self):
        """测试从入口点加载插件"""
        from framework.core.plugin_manager import PluginManager

        manager = PluginManager()
        plugin = manager.load_plugin_from_entrypoint(
            "plugins.reports.markdown:MarkdownReportPlugin"
        )

        assert plugin is not None
        assert plugin.name == "markdown"
