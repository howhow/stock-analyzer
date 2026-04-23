"""TestDCFIntegration - 从 test_phase0_integration.py 迁移"""

import pytest

from framework.events import Events
from framework.trading.seasons.dcf import DCFValuation, MonteCarloDCFResult


class TestDCFIntegration:
    """DCF 蒙特卡洛估值集成测试"""

    def test_monte_carlo_dcf_basic(self) -> None:
        """测试蒙特卡洛 DCF 基本流程"""
        dcf = DCFValuation()

        # 构造测试数据
        current_fcf = 40.0  # 当前 FCF（亿元）
        shares_outstanding = 12.56  # 总股本（亿股）

        result = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="消费",
            simulations=500,
        )

        # 验证结果结构
        assert isinstance(result, MonteCarloDCFResult)
        assert result.mean > 0
        assert result.median > 0
        assert len(result.ci_95) == 2
        assert result.ci_95[0] < result.ci_95[1]
        assert len(result.distribution) == 500

    def test_monte_carlo_dcf_industry_discount_rates(self) -> None:
        """测试不同行业折现率影响"""
        dcf = DCFValuation()

        current_fcf = 40.0
        shares_outstanding = 12.56

        result_bank = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="银行",
            simulations=200,
        )
        result_tech = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="科技",
            simulations=200,
        )

        # 科技行业折现率更高，估值应该更低
        assert result_bank.mean > result_tech.mean

    def test_dcf_calculated_event(self) -> None:
        """测试 DCF 计算完成后发送 dcf_calculated 事件"""
        received: list[dict] = []

        @Events.dcf_calculated.connect
        def on_dcf(sender, **kwargs):
            received.append(kwargs)

        try:
            dcf = DCFValuation()
            dcf.calculate_monte_carlo(
                current_fcf=40.0,
                shares_outstanding=12.56,
                industry="消费",
                simulations=100,
            )

            assert len(received) >= 1
        finally:
            Events.dcf_calculated.disconnect(on_dcf)

    def test_dcf_performance_local_calculation(self) -> None:
        """测试 DCF 本地计算性能 < 3s"""
        import time

        dcf = DCFValuation()

        start = time.time()
        dcf.calculate_monte_carlo(
            current_fcf=40.0,
            shares_outstanding=12.56,
            industry="消费",
            simulations=1000,
        )
        elapsed = time.time() - start

        # 本地计算 < 3s
        assert elapsed < 3.0, f"DCF 计算 {elapsed:.2f}s 超过 3s 限制"


# ═══════════════════════════════════════════════════════════════
# Task 0.24: Phase 0 验收
# ═══════════════════════════════════════════════════════════════
