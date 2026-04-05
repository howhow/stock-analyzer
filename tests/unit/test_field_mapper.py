import pytest
"""
字段映射器单元测试
"""


from app.data.field_mapper import FieldMapper


class TestFieldMapper:
    """字段映射器测试"""

    def test_map_tushare_stock_code(self):
        """测试映射Tushare股票代码"""
        data = {"ts_code": "600519.SH", "name": "贵州茅台"}
        mapped = FieldMapper.map_tushare(data)
        assert mapped["stock_code"] == "600519.SH"
        assert mapped["name"] == "贵州茅台"

    def test_map_tushare_daily_quotes(self):
        """测试映射Tushare日线数据"""
        data = {
            "ts_code": "600519.SH",
            "trade_date": "20260401",
            "open": 1800.0,
            "close": 1820.0,
            "high": 1830.0,
            "low": 1790.0,
            "vol": 50000,
            "amount": 90000000,
        }
        mapped = FieldMapper.map_tushare(data)

        assert mapped["stock_code"] == "600519.SH"
        assert mapped["trade_date"] == "20260401"
        assert mapped["open"] == 1800.0
        assert mapped["volume"] == 50000

    def test_map_tushare_financial(self):
        """测试映射Tushare财务数据"""
        data = {
            "ts_code": "600519.SH",
            "ann_date": "20260331",
            "revenue": 1000000000,
            "net_profit": 500000000,
            "pe": 30.5,
            "pb": 8.2,
        }
        mapped = FieldMapper.map_tushare(data)

        assert mapped["report_date"] == "20260331"
        assert mapped["revenue"] == 1000000000
        assert mapped["pe_ratio"] == 30.5
        assert mapped["pb_ratio"] == 8.2

    def test_map_akshare_stock_info(self):
        """测试映射AKShare股票信息"""
        data = {
            "代码": "600519",
            "股票简称": "贵州茅台",
            "行业": "白酒",
        }
        mapped = FieldMapper.map_akshare(data)

        assert mapped["stock_code"] == "600519"
        assert mapped["name"] == "贵州茅台"
        assert mapped["industry"] == "白酒"

    def test_map_akshare_daily_quotes(self):
        """测试映射AKShare日线数据"""
        data = {
            "日期": "2026-04-01",
            "开盘": 1800.0,
            "收盘": 1820.0,
            "最高": 1830.0,
            "最低": 1790.0,
            "成交量": 50000,
            "成交额": 90000000,
        }
        mapped = FieldMapper.map_akshare(data)

        assert mapped["trade_date"] == "2026-04-01"
        assert mapped["open"] == 1800.0
        assert mapped["volume"] == 50000

    def test_map_batch(self):
        """测试批量映射"""
        data_list = [
            {"ts_code": "600519.SH", "name": "贵州茅台"},
            {"ts_code": "000001.SZ", "name": "平安银行"},
        ]
        mapped_list = FieldMapper.map_tushare_batch(data_list)

        assert len(mapped_list) == 2
        assert mapped_list[0]["stock_code"] == "600519.SH"
        assert mapped_list[1]["stock_code"] == "000001.SZ"

    def test_skip_none_values(self):
        """测试跳过None值"""
        data = {
            "ts_code": "600519.SH",
            "name": "贵州茅台",
            "industry": None,
        }
        mapped = FieldMapper.map_tushare(data)

        assert "stock_code" in mapped
        assert "name" in mapped
        assert "industry" not in mapped

    def test_unknown_field_kept(self):
        """测试未知字段保留"""
        data = {
            "ts_code": "600519.SH",
            "unknown_field": "value",
        }
        mapped = FieldMapper.map_tushare(data)

        assert mapped["stock_code"] == "600519.SH"
        assert mapped["unknown_field"] == "value"
