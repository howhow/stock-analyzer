"""
统一的 Mock 数据定义

所有测试用例应使用此文件中的 mock 数据，确保与 Pydantic 模型一致
"""

from datetime import date

# ============================================================
# 股票信息 Mock 数据
# ============================================================

MOCK_STOCK_INFO_DICT = {
    "code": "000001.SZ",
    "name": "平安银行",
    "market": "SZ",  # 必填字段
    "industry": "银行",
    "list_date": "1991-04-03",
}

MOCK_STOCK_INFO_DICT_2 = {
    "code": "600519.SH",
    "name": "贵州茅台",
    "market": "SH",  # 必填字段
    "industry": "白酒",
    "list_date": "2001-08-27",
}

# ============================================================
# 日线行情 Mock 数据
# ============================================================

MOCK_DAILY_QUOTES_DICT = [
    {
        "stock_code": "000001.SZ",
        "trade_date": "2024-01-01",
        "open": 10.5,
        "close": 10.8,
        "high": 11.0,
        "low": 10.3,
        "volume": 1000000.0,
        "amount": 10500000.0,
        "turnover_rate": 1.5,
    },
    {
        "stock_code": "000001.SZ",
        "trade_date": "2024-01-02",
        "open": 10.8,
        "close": 11.0,
        "high": 11.2,
        "low": 10.6,
        "volume": 1200000.0,
        "amount": 13000000.0,
        "turnover_rate": 1.8,
    },
]

# ============================================================
# 财务数据 Mock 数据
# ============================================================

MOCK_FINANCIAL_DATA_DICT = {
    "stock_code": "000001.SZ",
    "report_date": "2024-03-31",
    "revenue": 10000000000.0,
    "net_profit": 1000000000.0,
    "total_assets": 50000000000.0,
    "total_liabilities": 45000000000.0,
    "roe": 12.5,
    "pe_ratio": 8.5,
    "pb_ratio": 0.9,
}

# ============================================================
# 分时行情 Mock 数据
# ============================================================

MOCK_INTRADAY_QUOTES_DICT = [
    {
        "stock_code": "000001.SZ",
        "trade_time": "2024-01-01 09:30:00",
        "price": 10.5,
        "volume": 10000.0,
        "amount": 105000.0,
    },
    {
        "stock_code": "000001.SZ",
        "trade_time": "2024-01-01 09:31:00",
        "price": 10.6,
        "volume": 12000.0,
        "amount": 127200.0,
    },
]

# ============================================================
# Mock 数据生成器
# ============================================================


def create_stock_info_dict(
    code: str = "000001.SZ",
    name: str = "平安银行",
    market: str = "SZ",
    industry: str = "银行",
    list_date: str = "1991-04-03",
) -> dict:
    """
    创建股票信息字典

    Args:
        code: 股票代码
        name: 股票名称
        market: 市场（必填）
        industry: 行业
        list_date: 上市日期

    Returns:
        股票信息字典
    """
    return {
        "code": code,
        "name": name,
        "market": market,
        "industry": industry,
        "list_date": list_date,
    }


def create_daily_quote_dict(
    stock_code: str = "000001.SZ",
    trade_date: str = "2024-01-01",
    open_price: float = 10.5,
    close: float = 10.8,
    high: float = 11.0,
    low: float = 10.3,
    volume: float = 1000000.0,
    amount: float = 10500000.0,
) -> dict:
    """
    创建日线行情字典

    Args:
        stock_code: 股票代码
        trade_date: 交易日期
        open_price: 开盘价
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        amount: 成交额

    Returns:
        日线行情字典
    """
    return {
        "stock_code": stock_code,
        "trade_date": trade_date,
        "open": open_price,
        "close": close,
        "high": high,
        "low": low,
        "volume": volume,
        "amount": amount,
    }
