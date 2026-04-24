"""DCF 集成测试 — 使用真实 Tushare API"""

import pytest

from framework.trading.seasons.dcf import DCFValuation


@pytest.mark.integration
class TestDCFIntegration:
    """DCF 真实股票估值集成测试"""

    @pytest.mark.asyncio
    async def test_dcf_with_real_smic_data(self, smic_financial_data):
        """使用真实 SMIC 数据进行 DCF 估值"""
        dcf = DCFValuation()

        # 从真实数据提取参数（通过 DataHub 获取的聚合数据）
        current_price = smic_financial_data.get("current_price", 80.0)
        current_fcf = smic_financial_data.get("free_cash_flow", 50.0)
        shares = smic_financial_data.get("shares_outstanding", 10.0)

        result = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares,
            industry="科技",
            simulations=1000,
        )

        # 验证估值结果合理
        assert result.mean > 0
        assert result.ci_95[0] < result.mean < result.ci_95[1]

        # 与当前股价对比（±30% 合理区间）
        assert result.ci_95[0] * 0.7 <= current_price <= result.ci_95[1] * 1.3
