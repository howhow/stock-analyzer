"""测试指标接口协议"""

import pandas as pd
import pytest


class MockIndicator:
    """模拟指标实现"""

    @property
    def name(self) -> str:
        return "MockIndicator"

    @property
    def params(self) -> dict:
        return {"period": {"type": "int", "default": 14}}

    @property
    def description(self) -> str:
        return "Mock indicator for testing"

    @property
    def required_columns(self) -> list[str]:
        return ["close"]

    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        return data["close"].rolling(window=14).mean()

    def validate_params(self, **kwargs) -> bool:
        return True


class TestIndicatorInterface:
    """测试指标接口"""

    def test_mock_implementation_satisfies_interface(self):
        """验证模拟实现满足接口"""
        mock = MockIndicator()

        assert mock.name == "MockIndicator"
        assert "period" in mock.params

    def test_calculate_returns_series(self):
        """验证 calculate 返回 Series"""
        mock = MockIndicator()
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104] * 10})
        result = mock.calculate(data)

        assert isinstance(result, pd.Series)
