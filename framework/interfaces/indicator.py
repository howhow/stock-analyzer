"""
指标接口协议

定义用户可自定义的技术指标接口。
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class IndicatorInterface(Protocol):
    """
    指标接口协议

    用户可自定义指标插件，实现此接口即可被框架识别和使用。
    """

    @property
    def name(self) -> str:
        """
        指标名称

        Returns:
            指标名称（如 'RSI', 'MACD', '自定义指标'）
        """
        ...

    @property
    def params(self) -> dict[str, Any]:
        """
        指标参数定义

        Returns:
            参数定义字典，格式：
            {
                'param_name': {
                    'type': 'int' | 'float' | 'str' | 'bool',
                    'default': default_value,
                    'description': '参数说明',
                    'min': min_value,  # 可选
                    'max': max_value,  # 可选
                }
            }
        """
        ...

    @property
    def description(self) -> str:
        """
        指标描述

        Returns:
            指标的详细说明
        """
        ...

    @property
    def required_columns(self) -> list[str]:
        """
        计算所需的列名

        Returns:
            所需列名列表（如 ['close', 'high', 'low']）
        """
        ...

    def calculate(
        self,
        data: pd.DataFrame,
        **kwargs,
    ) -> pd.Series | pd.DataFrame:
        """
        计算指标

        Args:
            data: 输入数据（必须包含 required_columns）
            **kwargs: 指标参数（覆盖默认参数）

        Returns:
            计算结果（Series 或 DataFrame）

        Raises:
            ValueError: 参数错误
            KeyError: 缺少必要列
        """
        ...

    def validate_params(self, **kwargs) -> bool:
        """
        验证参数

        Args:
            **kwargs: 待验证的参数

        Returns:
            True 如果参数有效

        Raises:
            ValueError: 参数无效
        """
        ...
