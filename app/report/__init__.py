"""
报告生成模块
"""

from app.report.generator import ReportGenerator
from app.report.markdown_report import MarkdownReportGenerator
from app.report.storage import ReportStorage

__all__ = [
    "ReportGenerator",
    "MarkdownReportGenerator",
    "ReportStorage",
]
