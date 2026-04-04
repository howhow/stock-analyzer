"""
字段映射器

将不同数据源的字段映射到统一格式
"""

from typing import Any


class FieldMapper:
    """
    字段映射器

    负责将Tushare/AKShare的字段映射到统一的字段名
    """

    # Tushare → 统一字段映射
    TUSHARE_FIELD_MAP: dict[str, str] = {
        "ts_code": "stock_code",
        "trade_date": "trade_date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "vol": "volume",
        "amount": "amount",
        "turnover_rate": "turnover_rate",
        "name": "name",
        "industry": "industry",
        "list_date": "list_date",
        "market": "market",
        "ann_date": "report_date",
        "revenue": "revenue",
        "net_profit": "net_profit",
        "total_assets": "total_assets",
        "total_liab": "total_liabilities",
        "roe": "roe",
        "pe": "pe_ratio",
        "pb": "pb_ratio",
        "debt_to_assets": "debt_ratio",
    }

    # AKShare → 统一字段映射
    AKSHARE_FIELD_MAP: dict[str, str] = {
        "代码": "stock_code",
        "股票代码": "stock_code",
        "日期": "trade_date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover_rate",
        "股票简称": "name",
        "行业": "industry",
        "上市日期": "list_date",
        "市场": "market",
        "报告期": "report_date",
        "营业收入": "revenue",
        "净利润": "net_profit",
        "总资产": "total_assets",
        "总负债": "total_liabilities",
        "净资产收益率": "roe",
        "市盈率": "pe_ratio",
        "市净率": "pb_ratio",
        "资产负债率": "debt_ratio",
    }

    @classmethod
    def map_tushare(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        映射Tushare数据

        Args:
            data: Tushare原始数据

        Returns:
            映射后的数据
        """
        return cls._map_fields(data, cls.TUSHARE_FIELD_MAP)

    @classmethod
    def map_akshare(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        映射AKShare数据

        Args:
            data: AKShare原始数据

        Returns:
            映射后的数据
        """
        return cls._map_fields(data, cls.AKSHARE_FIELD_MAP)

    @classmethod
    def _map_fields(
        cls, data: dict[str, Any], field_map: dict[str, str]
    ) -> dict[str, Any]:
        """
        执行字段映射

        Args:
            data: 原始数据
            field_map: 字段映射表

        Returns:
            映射后的数据
        """
        mapped: dict[str, Any] = {}
        for old_key, value in data.items():
            new_key = field_map.get(old_key, old_key)
            # 跳过None值
            if value is not None:
                mapped[new_key] = value
        return mapped

    @classmethod
    def map_tushare_batch(cls, data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量映射Tushare数据"""
        return [cls.map_tushare(item) for item in data_list]

    @classmethod
    def map_akshare_batch(cls, data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量映射AKShare数据"""
        return [cls.map_akshare(item) for item in data_list]
