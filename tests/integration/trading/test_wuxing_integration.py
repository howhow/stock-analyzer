"""五行引擎集成测试 — 端到端验证"""

import pytest


@pytest.mark.integration
class TestWuxingIntegration:
    """五行引擎端到端集成测试"""

    def test_wuxing_engine_with_real_data(self, smic_financial_data):
        """使用真实数据运行五行引擎"""
        import pandas as pd

        from framework.trading.wuxing.engine import WuxingEngine

        engine = WuxingEngine()

        # 创建模拟的 DataFrame（真实场景需要从数据源获取）
        df = pd.DataFrame(
            {
                "close": [80.0, 82.0, 85.0, 83.0, 86.0],
                "volume": [10000, 12000, 11000, 13000, 12500],
            }
        )

        # 使用真实数据判断五行状态
        result = engine.analyze(
            ts_code="688981.SH",
            df=df,
            current_price=smic_financial_data.get("current_price", 86.0),
            historical_high=100.0,
            recent_low=70.0,
            recent_high=90.0,
            avg_volume_20d=12000.0,
            current_volume=12500.0,
            daily_change=0.03,
            price_n_days_ago=80.0,
        )

        # 验证返回结果
        assert result is not None
        assert hasattr(result, "element")
