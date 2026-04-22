"""标准接口模块。"""

from framework.interfaces.ai_provider import AIProviderInterface
from framework.interfaces.data_source import DataSourceInterface
from framework.interfaces.indicator import IndicatorInterface
from framework.interfaces.report import ReportInterface
from framework.interfaces.strategy import StrategyInterface

__all__ = [
    "DataSourceInterface",
    "AIProviderInterface",
    "IndicatorInterface",
    "StrategyInterface",
    "ReportInterface",
]
