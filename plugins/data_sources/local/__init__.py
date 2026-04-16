"""
Local 本地数据源插件

从本地 CSV/Parquet 文件加载历史数据，用于离线分析和回测。
"""

from .plugin import LocalPlugin, LocalPluginConfig
from .loader import LocalDataLoader
from .mapper import QuoteMapper

__all__ = [
    "LocalPlugin",
    "LocalPluginConfig",
    "LocalDataLoader",
    "QuoteMapper",
]
