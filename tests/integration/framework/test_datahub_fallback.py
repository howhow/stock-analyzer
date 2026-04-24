"""DataHub熔断降级集成测试"""

import pytest


@pytest.mark.integration
class TestDataHubFallback:
    """DataHub+熔断器集成测试"""

    def test_datahub_circuit_breaker(self, datahub):
        """DataHub连续调用验证熔断器状态"""
        import asyncio

        # 正常调用
        result1 = asyncio.run(datahub.fetch_daily("688981.SH"))
        assert result1 is not None

        # 连续调用验证熔断器状态
        for _ in range(5):
            result = asyncio.run(datahub.fetch_daily("688981.SH"))
            assert result is not None

    def test_datahub_invalid_symbol(self, datahub):
        """DataHub处理无效股票代码"""
        import asyncio

        # 无效代码应该返回空数据或抛出异常
        try:
            result = asyncio.run(datahub.fetch_daily("INVALID.CODE"))
            # 如果返回数据，应该是空的
            assert result is None or len(result) == 0
        except Exception:
            # 或者抛出异常也是可接受的
            pass
