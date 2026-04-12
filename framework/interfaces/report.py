"""
报告接口协议

定义用户可自定义的报告生成接口。
"""

from typing import Any, Protocol, runtime_checkable

from framework.models.analysis import AnalysisResult


@runtime_checkable
class ReportInterface(Protocol):
    """
    报告接口协议

    用户可自定义报告格式插件，实现此接口即可被框架识别和使用。
    """

    @property
    def name(self) -> str:
        """
        报告格式名称

        Returns:
            格式名称（如 'markdown', 'pdf', 'html'）
        """
        ...

    @property
    def file_extension(self) -> str:
        """
        文件扩展名

        Returns:
            扩展名（如 '.md', '.pdf', '.html'）
        """
        ...

    @property
    def content_type(self) -> str:
        """
        MIME类型

        Returns:
            MIME类型（如 'text/markdown', 'application/pdf'）
        """
        ...

    def generate(
        self,
        analysis_result: AnalysisResult,
        template: str | None = None,
        **kwargs,
    ) -> str | bytes:
        """
        生成报告

        Args:
            analysis_result: 分析结果
            template: 模板名称或路径（可选）
            **kwargs: 额外参数

        Returns:
            报告内容（字符串或字节）
        """
        ...

    def render_to_file(
        self,
        analysis_result: AnalysisResult,
        output_path: str,
        template: str | None = None,
        **kwargs,
    ) -> str:
        """
        渲染报告到文件

        Args:
            analysis_result: 分析结果
            output_path: 输出路径
            template: 模板名称或路径（可选）
            **kwargs: 额外参数

        Returns:
            生成的文件路径
        """
        ...
