"""
AKShare 数据源插件

提供 A 股行情数据获取功能，基于 AKShare 开源财经数据接口。

使用示例：
    from plugins.data_sources.akshare import AKSharePlugin

    # 创建插件实例
    plugin = AKSharePlugin()

    # 获取历史行情
    quotes = await plugin.get_quotes(
        stock_code="600519.SH",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    # 获取实时行情
    quote = await plugin.get_realtime_quote("600519.SH")

    # 健康检查
    is_healthy = await plugin.health_check()

    # 获取股票列表
    stocks = await plugin.get_supported_stocks("SH")
"""

from .plugin import AKSharePlugin

__all__ = ["AKSharePlugin"]
__version__ = "1.0.0"
