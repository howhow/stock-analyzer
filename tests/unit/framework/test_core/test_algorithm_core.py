"""测试算法核心模块"""

import pytest

from framework.core.algorithm_core import AlgorithmCore


class TestAlgorithmCore:
    """测试 AlgorithmCore"""

    def test_init(self):
        """测试初始化"""
        core = AlgorithmCore()

        assert core._indicators == {}

    def test_register_indicator(self):
        """测试注册指标"""
        from tests.unit.framework.test_interfaces.test_indicator_interface import (
            MockIndicator,
        )

        core = AlgorithmCore()
        mock = MockIndicator()
        core.register_indicator(mock)

        assert "MockIndicator" in core._indicators

    def test_get_indicator(self):
        """测试获取指标"""
        from tests.unit.framework.test_interfaces.test_indicator_interface import (
            MockIndicator,
        )

        core = AlgorithmCore()
        mock = MockIndicator()
        core.register_indicator(mock)

        result = core.get_indicator("MockIndicator")

        assert result is not None
        assert result.name == "MockIndicator"

    def test_get_indicator_not_found(self):
        """测试获取不存在的指标"""
        core = AlgorithmCore()

        result = core.get_indicator("NonExistent")

        assert result is None

    def test_list_indicators(self):
        """测试列出指标"""
        from tests.unit.framework.test_interfaces.test_indicator_interface import (
            MockIndicator,
        )

        core = AlgorithmCore()
        mock = MockIndicator()
        core.register_indicator(mock)

        indicators = core.list_indicators()

        assert "MockIndicator" in indicators

    @pytest.mark.asyncio
    async def test_calculate_indicator_not_implemented(self):
        """测试 calculate_indicator 指标未找到"""
        import pandas as pd

        from framework.core.algorithm_core import IndicatorNotFoundError

        core = AlgorithmCore()
        df = pd.DataFrame({"close": [1.0, 2.0, 3.0]})

        with pytest.raises(IndicatorNotFoundError):
            await core.calculate_indicator("nonexistent", df)
