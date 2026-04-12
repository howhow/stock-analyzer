"""
策略接口协议

定义用户可自定义的交易策略接口。
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class StrategyInterface(Protocol):
    """
    策略接口协议

    用户可自定义交易策略插件，实现此接口即可被框架识别和使用。
    """

    @property
    def name(self) -> str:
        """
        策略名称

        Returns:
            策略名称（如 '双均线策略', 'RSI反转策略'）
        """
        ...

    @property
    def params(self) -> dict[str, Any]:
        """
        策略参数定义

        Returns:
            参数定义字典
        """
        ...

    @property
    def description(self) -> str:
        """
        策略描述

        Returns:
            策略的详细说明
        """
        ...

    @property
    def time_horizon(self) -> str:
        """
        时间维度

        Returns:
            'short' | 'medium' | 'long'
        """
        ...

    def generate_signals(
        self,
        data: pd.DataFrame,
        indicators: dict[str, pd.Series],
        **kwargs,
    ) -> pd.Series:
        """
        生成交易信号

        Args:
            data: 行情数据
            indicators: 指标数据字典
            **kwargs: 策略参数

        Returns:
            信号序列（1: 买入, -1: 卖出, 0: 无信号）
        """
        ...

    def backtest(
        self,
        data: pd.DataFrame,
        indicators: dict[str, pd.Series],
        initial_capital: float = 100000,
        **kwargs,
    ) -> dict[str, Any]:
        """
        回测策略

        Args:
            data: 行情数据
            indicators: 指标数据字典
            initial_capital: 初始资金
            **kwargs: 策略参数

        Returns:
            回测结果，包含：
            {
                'total_return': 总收益率,
                'annualized_return': 年化收益率,
                'sharpe_ratio': 夏普比率,
                'max_drawdown': 最大回撤,
                'win_rate': 胜率,
                'trades': 交易记录列表,
            }
        """
        ...

    def validate_params(self, **kwargs) -> bool:
        """
        验证参数

        Args:
            **kwargs: 待验证的参数

        Returns:
            True 如果参数有效
        """
        ...
