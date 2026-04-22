"""蒙特卡洛 DCF 估值单元测试

测试目标:
- 行业折现率配置
- FCF 历史计算
- 增长率推断
- 蒙特卡洛模拟
- 置信区间计算
- EventBus 集成
"""

import pytest
import numpy as np
import pandas as pd

from framework.trading.seasons.dcf import (
    DCFValuation,
    MonteCarloDCFResult,
    INDUSTRY_DISCOUNT_RATES,
)
from framework.events import Events


class TestIndustryDiscountRates:
    """行业折现率配置测试"""

    def test_all_industries_have_valid_ranges(self):
        """测试所有行业折现率区间有效"""
        for industry, (low, high) in INDUSTRY_DISCOUNT_RATES.items():
            assert 0 < low < high < 1, f"{industry}: {low}~{high} invalid"

    def test_default_exists(self):
        """测试默认折现率存在"""
        assert "default" in INDUSTRY_DISCOUNT_RATES

    def test_get_discount_rate_known_industry(self):
        """测试已知行业折现率获取"""
        dcf = DCFValuation()
        low, high = dcf.get_discount_rate_range("银行")
        assert low == 0.08
        assert high == 0.10

    def test_get_discount_rate_unknown_industry(self):
        """测试未知行业使用默认折现率"""
        dcf = DCFValuation()
        low, high = dcf.get_discount_rate_range("未知行业")
        default = INDUSTRY_DISCOUNT_RATES["default"]
        assert low == default[0]
        assert high == default[1]


class TestFCFHistory:
    """FCF 历史计算测试"""

    def test_calculate_fcf_history(self):
        """测试 FCF 计算: OCF - CapEx"""
        dcf = DCFValuation()
        df = pd.DataFrame(
            {
                "end_date": ["2022", "2023", "2024"],
                "n_cashflow_act": [100.0, 120.0, 130.0],
                "n_cashflow_inv_act": [-30.0, -40.0, -35.0],
            }
        )

        result = dcf.calculate_fcf_history(df)

        assert len(result) == 3
        assert "fcf" in result.columns
        assert result["ocf"].iloc[0] == 100.0
        assert result["capex"].iloc[0] == 30.0  # abs(-30)
        assert result["fcf"].iloc[0] == 70.0  # 100 - 30

    def test_fcf_history_with_positive_investment(self):
        """测试投资现金流为正的情况"""
        dcf = DCFValuation()
        df = pd.DataFrame(
            {
                "end_date": ["2023"],
                "n_cashflow_act": [100.0],
                "n_cashflow_inv_act": [10.0],  # 正数 = 投资收回
            }
        )

        result = dcf.calculate_fcf_history(df)
        assert result["capex"].iloc[0] == 10.0
        assert result["fcf"].iloc[0] == 90.0  # 100 - 10


class TestGrowthRateInference:
    """增长率推断测试"""

    def test_infer_from_sufficient_data(self):
        """测试从充足数据推断增长率"""
        dcf = DCFValuation()
        fcf_history = pd.DataFrame(
            {
                "end_date": ["2020", "2021", "2022", "2023", "2024"],
                "fcf": [50.0, 55.0, 60.0, 66.0, 72.0],
            }
        )

        low, high = dcf.infer_growth_rate_range(fcf_history)
        assert -0.10 <= low <= high <= 0.20

    def test_infer_from_insufficient_data(self):
        """测试数据不足时返回默认值"""
        dcf = DCFValuation()
        fcf_history = pd.DataFrame({"end_date": ["2023"], "fcf": [100.0]})

        low, high = dcf.infer_growth_rate_range(fcf_history)
        assert low == -0.05
        assert high == 0.05

    def test_infer_conservative_factor(self):
        """测试保守因子降低增长率"""
        dcf = DCFValuation()
        fcf_history = pd.DataFrame(
            {
                "end_date": ["2020", "2021", "2022", "2023", "2024"],
                "fcf": [50.0, 60.0, 72.0, 86.0, 103.0],  # 高增长
            }
        )

        low_normal, high_normal = dcf.infer_growth_rate_range(
            fcf_history, conservative_factor=1.0
        )
        low_conservative, high_conservative = dcf.infer_growth_rate_range(
            fcf_history, conservative_factor=0.5
        )

        # 保守因子应降低增长率
        assert low_conservative <= low_normal
        assert high_conservative <= high_normal


class TestMonteCarloSimulation:
    """蒙特卡洛模拟测试"""

    def test_basic_simulation(self):
        """测试基本蒙特卡洛模拟"""
        dcf = DCFValuation(default_simulations=100)
        result = dcf.calculate_monte_carlo(
            current_fcf=1e9,  # 10 亿
            shares_outstanding=1e9,  # 10 亿股
            industry="消费",
            seed=42,
        )

        assert isinstance(result, MonteCarloDCFResult)
        assert result.mean > 0
        assert result.median > 0
        assert result.std > 0
        assert result.simulations == 100

    def test_confidence_intervals(self):
        """测试置信区间"""
        dcf = DCFValuation(default_simulations=1000)
        result = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="银行",
            seed=42,
        )

        # 95% 区间应宽于 90% 区间
        assert result.ci_95[0] <= result.ci_90[0]
        assert result.ci_95[1] >= result.ci_90[1]

        # 均值应在 90% 区间内
        assert result.ci_90[0] <= result.mean <= result.ci_90[1]

    def test_deterministic_with_seed(self):
        """测试相同 seed 产生相同结果"""
        dcf = DCFValuation(default_simulations=100)

        result1 = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="科技",
            seed=42,
        )
        result2 = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="科技",
            seed=42,
        )

        assert result1.mean == result2.mean
        assert result1.median == result2.median

    def test_custom_growth_rate_range(self):
        """测试自定义增长率区间"""
        dcf = DCFValuation(default_simulations=100)
        result = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            growth_rate_range=(0.02, 0.08),
            seed=42,
        )

        assert result.growth_rate_range == (0.02, 0.08)

    def test_negative_fcf_raises(self):
        """测试 FCF 为负时抛出异常"""
        dcf = DCFValuation()
        with pytest.raises(ValueError, match="FCF is negative or zero"):
            import asyncio

            asyncio.run(
                dcf.analyze_stock(
                    ts_code="000001.SZ",
                    cashflow_df=pd.DataFrame(
                        {
                            "end_date": ["2023"],
                            "n_cashflow_act": [100.0],
                            "n_cashflow_inv_act": [-200.0],  # CapEx > OCF
                        }
                    ),
                    shares_outstanding=1e9,
                    industry="银行",
                )
            )

    def test_to_dict(self):
        """测试结果序列化"""
        dcf = DCFValuation(default_simulations=100)
        result = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            seed=42,
        )

        d = result.to_dict()
        assert "mean" in d
        assert "median" in d
        assert "ci_90" in d
        assert "ci_95" in d
        assert isinstance(d["ci_90"], list)
        assert len(d["ci_90"]) == 2

    def test_eventbus_integration(self):
        """测试 DCF 计算完成后发送 EventBus 事件"""
        dcf = DCFValuation(default_simulations=100)
        received = []

        @Events.dcf_calculated.connect
        def handler(sender, mean, median, industry, simulations, **kwargs):
            received.append(
                {
                    "mean": mean,
                    "median": median,
                    "industry": industry,
                    "simulations": simulations,
                }
            )

        try:
            dcf.calculate_monte_carlo(
                current_fcf=1e9,
                shares_outstanding=1e9,
                industry="医药",
                seed=42,
            )

            assert len(received) == 1
            assert received[0]["industry"] == "医药"
            assert received[0]["mean"] > 0
        finally:
            Events.dcf_calculated.disconnect(handler)

    def test_performance_under_3_seconds(self):
        """测试 DCF 计算性能 < 3 秒（1000 次模拟）"""
        import time

        dcf = DCFValuation(default_simulations=1000)

        start = time.time()
        dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="消费",
            seed=42,
        )
        elapsed = time.time() - start

        assert elapsed < 3.0, f"DCF took {elapsed:.2f}s, expected < 3s"

    def test_higher_discount_rate_lower_valuation(self):
        """测试高折现率导致低估值"""
        dcf = DCFValuation(default_simulations=500)

        # 银行：低折现率 (8-10%)
        result_bank = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="银行",
            seed=42,
        )

        # 科技：高折现率 (12-15%)
        result_tech = dcf.calculate_monte_carlo(
            current_fcf=1e9,
            shares_outstanding=1e9,
            industry="科技",
            seed=42,
        )

        # 高折现率 → 低估值
        assert result_bank.mean > result_tech.mean
