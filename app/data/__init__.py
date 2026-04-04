"""
数据获取模块

提供统一的股票数据获取接口
"""

from app.data.akshare_client import AKShareClient
from app.data.base import BaseDataSource, DataSourceError, DataSourceProtocol
from app.data.data_fetcher import DataFetcher
from app.data.field_mapper import FieldMapper
from app.data.health_check import HealthChecker, HealthStatus
from app.data.preprocessor import DataPreprocessor
from app.data.tushare_client import TushareClient

__all__ = [
    # 客户端
    "TushareClient",
    "AKShareClient",
    "DataFetcher",
    # 基类和协议
    "BaseDataSource",
    "DataSourceProtocol",
    "DataSourceError",
    # 工具类
    "FieldMapper",
    "DataPreprocessor",
    "HealthChecker",
    "HealthStatus",
]
