"""Tushare 数据源插件

提供 A 股专业数据源接口，包括深度财务数据、机构持仓等。
"""

from .plugin import TusharePlugin

__all__ = ["TusharePlugin"]
__version__ = "1.0.0"
