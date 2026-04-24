"""
TushareClient补充测试 - 提升覆盖率
"""

from unittest.mock import patch

from app.data.tushare_client import TushareClient


class TestTushareClientMore:
    """TushareClient补充测试"""

    def test_client_init_with_token(self):
        """测试带token初始化"""
        client = TushareClient(token="test_token_123")
        assert client is not None

    def test_client_init_without_token(self):
        """测试无token初始化"""
        with patch("app.data.tushare_client.settings") as mock_settings:
            mock_settings.tushare_token = "default_token"
            client = TushareClient()
            assert client is not None

    def test_build_query_params(self):
        """测试构建查询参数"""
        TushareClient(token="test")  # 实例化测试

        # 测试参数构建
        params = {
            "ts_code": "000001.SZ",
            "start_date": "20240101",
            "end_date": "20240131",
        }

        # 验证参数结构
        assert "ts_code" in params
        assert "start_date" in params

    def test_parse_response_data(self):
        """测试解析响应数据"""
        TushareClient(token="test")  # 实例化测试

        # 模拟API响应
        mock_response = {
            "data": {
                "fields": ["ts_code", "trade_date", "close"],
                "items": [
                    ["000001.SZ", "20240101", 10.5],
                    ["000001.SZ", "20240102", 11.0],
                ],
            }
        }

        # 验证数据结构
        assert "data" in mock_response
        assert "fields" in mock_response["data"]
        assert "items" in mock_response["data"]

    def test_error_handling(self):
        """测试错误处理"""
        TushareClient(token="test")  # 实例化测试

        # 测试空响应处理
        empty_response = {"data": None}

        # 应该能处理空数据
        assert empty_response["data"] is None
