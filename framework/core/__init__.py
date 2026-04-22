"""核心模块。"""

from framework.core.algorithm_core import AlgorithmCore
from framework.core.data_core import DataCore
from framework.core.plugin_manager import PluginManager

__all__ = [
    "DataCore",
    "AlgorithmCore",
    "PluginManager",
]
