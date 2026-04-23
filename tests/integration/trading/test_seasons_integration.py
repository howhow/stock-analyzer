"""四季引擎集成测试 — 端到端验证"""

import pytest


@pytest.mark.integration
class TestSeasonsIntegration:
    """四季引擎端到端集成测试"""

    def test_seasons_engine_with_real_data(self, smic_financial_data):
        """使用真实数据运行四季引擎"""
        from framework.trading.seasons.engine import SeasonsEngine

        engine = SeasonsEngine()

        # 使用真实数据判断季节
        result = engine.analyze(
            ts_code="688981.SH",
            dcf_value=smic_financial_data.get("dcf_value", 100.0),
            current_price=smic_financial_data.get("current_price", 80.0),
        )

        # 验证返回结果
        assert result is not None
        assert hasattr(result, "season")
        assert result.season is not None
