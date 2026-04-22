"""蒙特卡洛 DCF 估值模块

设计原则:
- 行业折现率区间：基于 CAPM 行业 β + 无风险利率 + 风险溢价
- FCF 计算：OCF - CapEx（经营现金流 - 资本支出）
- 增长率推断：从历史 FCF 数据推断增长率分布
- 蒙特卡洛模拟：1000 次采样，生成估值分布
- 置信区间：输出 ci_90, ci_95 区间

硬依赖：numpy, pandas（已满足）
可选依赖：无（纯 numpy 实现）
"""

from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd

from framework.events import Events


# ═══════════════════════════════════════════════════════════════
# 行业折现率配置
# ═══════════════════════════════════════════════════════════════

# 行业折现率区间配置
#
# 基于 CAPM 模型：
# r = r_f + β × (r_m - r_f)
#
# 其中：
# - r_f: 无风险利率（中国约 2.5-3%，取 3%）
# - r_m: 市场预期收益率（A股约 10-12%，取 10%）
# - β: 行业系统性风险系数
#
# 行业 β 参考值：
# - 银行: 0.5-0.7（低波动，稳定行业）
# - 消费: 0.8-1.0（中等波动）
# - 科技: 1.2-1.5（高波动，成长型）
# - 医药: 1.0-1.3（中等偏高波动）
# - 能源: 1.0-1.2（周期性行业）
# - 制造: 0.9-1.1（传统行业）
#
# 计算示例（银行）：
# r = 3% + 0.6 × (10% - 3%) = 3% + 4.2% = 7.2%
# 区间取 8-10%（保守调整）
#
# 来源：
# - 中国十年期国债收益率约 2.5-3%
# - A股历史平均收益率约 10-12%
# - 行业 β 参考 Wind/中证指数数据

INDUSTRY_DISCOUNT_RATES: Dict[str, Tuple[float, float]] = {""
    "银行": (0.08, 0.10),
    "消费": (0.10, 0.12),
    "食品饮料": (0.10, 0.12),
    "科技": (0.12, 0.15),
    "电子": (0.12, 0.15),
    "计算机": (0.12, 0.15),
    "医药": (0.11, 0.13),
    "医药生物": (0.11, 0.13),
    "能源": (0.10, 0.12),
    "石油石化": (0.10, 0.12),
    "制造": (0.09, 0.11),
    "机械": (0.09, 0.11),
    "汽车": (0.09, 0.11),
    "房地产": (0.12, 0.14),  # 高风险行业
    "保险": (0.09, 0.11),
    "证券": (0.11, 0.13),
    "公用事业": (0.07, 0.09),  # 低波动，稳定现金流
    "电力": (0.07, 0.09),
    "水务": (0.07, 0.09),
    "交通运输": (0.08, 0.10),
    "通信": (0.10, 0.12),
    "传媒": (0.11, 0.13),
    "农林牧渔": (0.11, 0.13),
    "化工": (0.10, 0.12),
    "有色金属": (0.11, 0.13),
    "钢铁": (0.10, 0.12),
    "煤炭": (0.10, 0.12),
    "default": (0.10, 0.12),  # 默认区间
}


@dataclass
class MonteCarloDCFResult:
    """蒙特卡洛 DCF 结果

    Attributes:
        mean: 估值均值（元/股）
        median: 估值中位数（元/股）
        std: 估值标准差
        ci_90: 90% 置信区间 [lower, upper]
        ci_95: 95% 置信区间 [lower, upper]
        distribution: 估值分布数组（用于可视化）
        discount_rate_range: 折现率区间 [min, max]
        growth_rate_range: 增长率区间 [min, max]
        simulations: 模拟次数
        fcf_history: FCF 历史数据（用于回溯）
    """

    mean: float
    median: float
    std: float
    ci_90: Tuple[float, float]
    ci_95: Tuple[float, float]
    distribution: np.ndarray
    discount_rate_range: Tuple[float, float]
    growth_rate_range: Tuple[float, float]
    simulations: int
    fcf_history: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（便于 JSON 序列化）"""
        return {
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "ci_90": list(self.ci_90),
            "ci_95": list(self.ci_95),
            "discount_rate_range": list(self.discount_rate_range),
            "growth_rate_range": list(self.growth_rate_range),
            "simulations": self.simulations,
        }


class DCFValuation:
    """蒙特卡洛 DCF 估值

    Args:
        default_simulations: 默认模拟次数（默认 1000）
        projection_years: 预测年限（默认 10 年）
        terminal_growth: 永续增长率（默认 3%，接近 GDP 增长）
    """

    def __init__(
        self,
        default_simulations: int = 1000,
        projection_years: int = 10,
        terminal_growth: float = 0.03,
    ):
        self._simulations = default_simulations
        self._projection_years = projection_years
        self._terminal_growth = terminal_growth

    def get_discount_rate_range(self, industry: str) -> Tuple[float, float]:
        """获取行业折现率区间

        Args:
            industry: 行业名称

        Returns:
            (min_rate, max_rate) 折现率区间
        """
        return INDUSTRY_DISCOUNT_RATES.get(industry, INDUSTRY_DISCOUNT_RATES["default"])

    def calculate_fcf_history(
        self,
        cashflow_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """计算 FCF 历史数据

        FCF = OCF - CapEx（经营现金流 - 资本支出）

        Args:
            cashflow_df: 现金流量表数据，需包含：
                - end_date: 报告期
                - n_cashflow_act: 经营活动产生的现金流量净额
                - n_cashflow_inv_act: 投资活动产生的现金流量净额（负数为资本支出）

        Returns:
            DataFrame with columns: end_date, ocf, capex, fcf
        """
        # 提取必要列
        df = cashflow_df.copy()

        # OCF: 经营现金流
        df["ocf"] = df["n_cashflow_act"]

        # CapEx: 资本支出（投资现金流流出，通常为负数，取绝对值）
        # 注意：投资现金流净额为负数表示现金流出，资本支出 = -n_cashflow_inv_act
        # 但实际数据可能需要筛选 "购建固定资产、无形资产和其他长期资产支付的现金"
        # Tushare 字段: n_cashflow_inv_act（投资活动现金流出小计，负数）
        # 简化处理：CapEx = -min(n_cashflow_inv_act, 0) 或直接取 invest_cash_acc 处理
        df["capex"] = np.abs(df.get("n_cashflow_inv_act", 0))

        # FCF = OCF - CapEx
        df["fcf"] = df["ocf"] - df["capex"]

        return df[["end_date", "ocf", "capex", "fcf"]]

    def infer_growth_rate_range(
        self,
        fcf_history: pd.DataFrame,
        conservative_factor: float = 0.8,
    ) -> Tuple[float, float]:
        """从历史 FCF 数据推断增长率区间

        使用历史 FCF 年增长率的标准差作为波动性参考，
        并应用保守因子降低预期增长率。

        Args:
            fcf_history: FCF 历史数据，需包含 fcf 列
            conservative_factor: 保守因子（默认 0.8，降低 20%）

        Returns:
            (min_growth, max_growth) 增长率区间
        """
        fcf_values = fcf_history["fcf"].values

        if len(fcf_values) < 3:
            # 数据不足，使用保守默认值
            return (-0.05, 0.05)

        # 计算历史增长率
        growth_rates = []
        for i in range(1, len(fcf_values)):
            if fcf_values[i - 1] > 0 and fcf_values[i] > 0:
                g = (fcf_values[i] - fcf_values[i - 1]) / fcf_values[i - 1]
                growth_rates.append(g)

        if len(growth_rates) < 2:
            return (-0.05, 0.05)

        # 使用历史增长率均值 ± 标准差
        mean_g = np.mean(growth_rates) * conservative_factor
        std_g = np.std(growth_rates)

        # 设置区间边界
        min_g = max(mean_g - std_g, -0.10)  # 下限不低于 -10%
        max_g = min(mean_g + std_g, 0.20)  # 上限不超过 20%

        return (min_g, max_g)

    def calculate_monte_carlo(
        self,
        current_fcf: float,
        shares_outstanding: float,
        industry: str = "default",
        growth_rate_range: Optional[Tuple[float, float]] = None,
        simulations: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> MonteCarloDCFResult:
        """蒙特卡洛 DCF 估值模拟

        流程：
        1. 获取行业折现率区间
        2. 获取增长率区间（或从历史推断）
        3. 随机采样折现率和增长率
        4. 计算 FCF 预测序列
        5. 计算终值（Terminal Value）
        6. 折现求和得到企业价值
        7. 除以股本得到每股估值
        8. 重复 simulations 次，生成分布

        Args:
            current_fcf: 当前年度 FCF（元）
            shares_outstanding: 总股本（股）
            industry: 行业名称（用于获取折现率）
            growth_rate_range: 增长率区间（可选，默认推断）
            simulations: 模拟次数（可选，默认 1000）
            seed: 随机种子（用于可重复测试）

        Returns:
            MonteCarloDCFResult 估值结果
        """
        if seed is not None:
            np.random.seed(seed)

        n_sim = simulations or self._simulations

        # 获取折现率区间
        dr_range = self.get_discount_rate_range(industry)

        # 增长率区间（保守估计）
        gr_range = growth_rate_range or (-0.05, 0.08)

        # 随机采样
        discount_rates = np.random.uniform(dr_range[0], dr_range[1], n_sim)
        growth_rates = np.random.uniform(gr_range[0], gr_range[1], n_sim)

        # DCF 计算
        valuations = np.zeros(n_sim)

        for i in range(n_sim):
            r = discount_rates[i]
            g = growth_rates[i]

            # 预测期 FCF 序列
            fcf_forecast = np.zeros(self._projection_years)
            fcf_forecast[0] = current_fcf * (1 + g)

            for j in range(1, self._projection_years):
                # 增长率逐年衰减（更保守）
                decay_factor = 0.95**j  # 每年衰减 5%
                fcf_forecast[j] = fcf_forecast[j - 1] * (1 + g * decay_factor)

            # 终值（Terminal Value）
            terminal_fcf = fcf_forecast[-1] * (1 + self._terminal_growth)
            terminal_value = terminal_fcf / (r - self._terminal_growth)

            # 折现求和
            discount_factors = (1 + r) ** np.arange(1, self._projection_years + 1)
            pv_fcf = np.sum(fcf_forecast / discount_factors)
            pv_terminal = terminal_value / discount_factors[-1]

            # 企业价值
            enterprise_value = pv_fcf + pv_terminal

            # 每股估值
            valuations[i] = enterprise_value / shares_outstanding

        # 计算统计量
        mean_val = np.mean(valuations)
        median_val = np.median(valuations)
        std_val = np.std(valuations)

        # 置信区间
        ci_90 = (np.percentile(valuations, 5), np.percentile(valuations, 95))
        ci_95 = (np.percentile(valuations, 2.5), np.percentile(valuations, 97.5))

        # 发送事件
        Events.dcf_calculated.send(
            self,
            mean=mean_val,
            median=median_val,
            industry=industry,
            simulations=n_sim,
        )

        return MonteCarloDCFResult(
            mean=mean_val,
            median=median_val,
            std=std_val,
            ci_90=ci_90,
            ci_95=ci_95,
            distribution=valuations,
            discount_rate_range=dr_range,
            growth_rate_range=gr_range,
            simulations=n_sim,
        )

    async def analyze_stock(
        self,
        ts_code: str,
        cashflow_df: pd.DataFrame,
        shares_outstanding: float,
        industry: str = "default",
        simulations: Optional[int] = None,
    ) -> MonteCarloDCFResult:
        """分析股票估值（异步接口）

        Args:
            ts_code: 股票代码
            cashflow_df: 现金流量表数据
            shares_outstanding: 总股本
            industry: 行业名称
            simulations: 模拟次数

        Returns:
            MonteCarloDCFResult 估值结果
        """
        # 计算 FCF 历史
        fcf_history = self.calculate_fcf_history(cashflow_df)

        # 推断增长率区间
        growth_range = self.infer_growth_rate_range(fcf_history)

        # 当前 FCF（取最近一年）
        current_fcf = fcf_history["fcf"].iloc[-1] if len(fcf_history) > 0 else 0

        if current_fcf <= 0:
            # FCF 为负，无法估值
            raise ValueError(f"FCF is negative or zero for {ts_code}")

        # 蒙特卡洛模拟
        result = self.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry=industry,
            growth_rate_range=growth_range,
            simulations=simulations,
        )

        # 保存 FCF 历史
        result.fcf_history = fcf_history

        return result
