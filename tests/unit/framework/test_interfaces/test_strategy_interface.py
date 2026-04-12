"""测试策略接口协议"""

import pandas as pd
import pytest


class MockStrategy:
    """模拟策略实现"""

    @property
    def name(self) -> str:
        return "MockStrategy"

    @property
    def params(self) -> dict:
        return {}

    @property
    def description(self) -> str:
        return "Mock strategy for testing"

    @property
    def time_horizon(self) -> str:
        return "short"

    def generate_signals(
        self, data: pd.DataFrame, indicators: dict[str, pd.Series], **kwargs
    ) -> pd.Series:
        return pd.Series([0] * len(data))

    def backtest(
        self,
        data: pd.DataFrame,
        indicators: dict[str, pd.Series],
        initial_capital: float = 100000,
        **kwargs,
    ) -> dict:
        return {
            "total_return": 0.1,
            "annualized_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.05,
            "win_rate": 0.6,
            "trades": [],
        }

    def validate_params(self, **kwargs) -> bool:
        return True


class TestStrategyInterface:
    """测试策略接口"""

    def test_mock_implementation_satisfies_interface(self):
        """验证模拟实现满足接口"""
        mock = MockStrategy()

        assert mock.name == "MockStrategy"
        assert mock.time_horizon == "short"

    def test_generate_signals_returns_series(self):
        """验证 generate_signals 返回 Series"""
        mock = MockStrategy()
        data = pd.DataFrame({"close": [100, 101, 102]})
        signals = mock.generate_signals(data, {})

        assert isinstance(signals, pd.Series)

    def test_backtest_returns_dict(self):
        """验证 backtest 返回字典"""
        mock = MockStrategy()
        data = pd.DataFrame({"close": [100, 101, 102]})
        result = mock.backtest(data, {})

        assert "total_return" in result
        assert "sharpe_ratio" in result
