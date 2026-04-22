"""
算法核心模块

统一算法管理和调度。
"""

import asyncio
from inspect import signature
from typing import TYPE_CHECKING, Any, Callable

import pandas as pd

from app.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    momentum,
    money_flow_index,
    obv,
    rate_of_change,
    rsi,
    sma,
    stochastic_oscillator,
    williams_r,
)
from app.utils.logger import get_logger
from framework.interfaces.ai_provider import AIProviderInterface
from framework.interfaces.indicator import IndicatorInterface

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


# ============================================================================
# 自定义异常类
# ============================================================================


class IndicatorNotFoundError(Exception):
    """指标未找到"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Indicator not found: {name}")


class IndicatorCalculationError(Exception):
    """指标计算失败"""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"Indicator calculation failed '{name}': {reason}")


class AIProviderNotFoundError(Exception):
    """AI提供商未找到"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"AI provider not found: {name}")


class AIAnalysisError(Exception):
    """AI分析失败"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"AI analysis failed: {reason}")


# ============================================================================
# 内置指标映射
# ============================================================================

# 内置指标函数签名：
# - 一元指标（只需 close）: rsi, sma, ema, momentum, rate_of_change, obv, williams_r
# - 三元指标（需要 high/low/close）: atr, stochastic_oscillator
# - 多元指标（需要 volume）: money_flow_index, obv
# - 复合指标（返回 dict）: macd, bollinger_bands, stochastic_oscillator

BUILTIN_INDICATORS: dict[str, Callable[..., Any]] = {
    # 趋势指标
    "sma": sma,
    "ema": ema,
    "macd": macd,
    "bollinger_bands": bollinger_bands,
    # 动量指标
    "rsi": rsi,
    "momentum": momentum,
    "rate_of_change": rate_of_change,
    "stochastic_oscillator": stochastic_oscillator,
    "williams_r": williams_r,
    # 波动率指标
    "atr": atr,
    # 成交量指标
    "obv": obv,
    "money_flow_index": money_flow_index,
}


# 指标所需列映射
INDICATOR_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "sma": ["close"],
    "ema": ["close"],
    "macd": ["close"],
    "bollinger_bands": ["close"],
    "rsi": ["close"],
    "momentum": ["close"],
    "rate_of_change": ["close"],
    "williams_r": ["high", "low", "close"],
    "stochastic_oscillator": ["high", "low", "close"],
    "atr": ["high", "low", "close"],
    "obv": ["close", "volume"],
    "money_flow_index": ["high", "low", "close", "volume"],
}


# ============================================================================
# AlgorithmCore 类实现
# ============================================================================


class AlgorithmCore:
    """
    算法核心

    职责：
    1. 指标计算：调用TA-Lib或自定义指标
    2. AI辅助：调用AI提供商进行分析
    3. 算法编排：组合多个算法生成结果

    Example:
        >>> core = AlgorithmCore()
        >>> 
        >>> # 计算单个指标
        >>> rsi_result = await core.calculate_indicator('rsi', df, period=14)
        >>> 
        >>> # 批量计算指标
        >>> results = await core.calculate_indicators(df, ['rsi', 'macd', 'sma'])
        >>> 
        >>> # AI分析
        >>> analysis = await core.analyze_with_ai({'close': [1, 2, 3]}, '预测趋势')
    """

    def __init__(self):
        """初始化算法核心"""
        self._indicators: dict[str, IndicatorInterface] = {}
        self._ai_providers: dict[str, AIProviderInterface] = {}
        logger.info("AlgorithmCore initialized")

    # ========================================================================
    # 指标管理
    # ========================================================================

    def register_indicator(self, indicator: IndicatorInterface) -> None:
        """
        注册自定义指标

        Args:
            indicator: 指标实例
        """
        self._indicators[indicator.name] = indicator
        logger.info("Custom indicator registered", indicator=indicator.name)

    def get_indicator(self, name: str) -> IndicatorInterface | None:
        """
        获取已注册的自定义指标

        Args:
            name: 指标名称

        Returns:
            指标实例，如果不存在返回 None
        """
        return self._indicators.get(name)

    def list_indicators(self) -> list[str]:
        """
        获取所有可用指标列表（自定义 + 内置）

        Returns:
            指标名称列表
        """
        custom = list(self._indicators.keys())
        builtin = list(BUILTIN_INDICATORS.keys())
        return list(set(custom + builtin))

    def list_custom_indicators(self) -> list[str]:
        """
        获取已注册的自定义指标列表

        Returns:
            自定义指标名称列表
        """
        return list(self._indicators.keys())

    # ========================================================================
    # AI提供商管理
    # ========================================================================

    def register_ai_provider(self, provider: AIProviderInterface) -> None:
        """
        注册AI提供商

        Args:
            provider: AI提供商实例
        """
        self._ai_providers[provider.name] = provider
        logger.info(
            "AI provider registered",
            provider=provider.name,
            models=provider.supported_models,
        )

    def get_ai_provider(self, name: str) -> AIProviderInterface | None:
        """
        获取AI提供商

        Args:
            name: 提供商名称

        Returns:
            AI提供商实例，如果不存在返回 None
        """
        return self._ai_providers.get(name)

    def list_ai_providers(self) -> list[str]:
        """
        获取已注册的AI提供商列表

        Returns:
            AI提供商名称列表
        """
        return list(self._ai_providers.keys())

    # ========================================================================
    # 指标计算
    # ========================================================================

    async def calculate_indicator(
        self,
        name: str,
        data: pd.DataFrame,
        **kwargs,
    ) -> pd.Series | pd.DataFrame:
        """
        计算单个指标

        Args:
            name: 指标名称
            data: 输入数据（DataFrame，必须包含所需列）
            **kwargs: 指标参数

        Returns:
            计算结果（Series 或 DataFrame）

        Raises:
            IndicatorNotFoundError: 指标未找到
            IndicatorCalculationError: 指标计算失败

        Example:
            >>> df = pd.DataFrame({'close': [1, 2, 3, 4, 5]})
            >>> rsi = await core.calculate_indicator('rsi', df, period=14)
            >>> 
            >>> df2 = pd.DataFrame({
            ...     'high': [10, 11, 12],
            ...     'low': [8, 9, 10],
            ...     'close': [9, 10, 11]
            ... })
            >>> atr = await core.calculate_indicator('atr', df2, period=14)
        """
        logger.debug(
            "Calculating indicator",
            indicator=name,
            data_shape=data.shape,
            params=kwargs,
        )

        try:
            # 1. 检查是否是注册的自定义指标
            if name in self._indicators:
                custom_indicator = self._indicators[name]
                
                # 验证所需列
                missing_cols = [
                    col for col in custom_indicator.required_columns
                    if col not in data.columns
                ]
                if missing_cols:
                    raise IndicatorCalculationError(
                        name,
                        f"Missing required columns: {missing_cols}",
                    )
                
                # 调用自定义指标（在线程池中执行同步函数）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: custom_indicator.calculate(data, **kwargs)
                )
                
                logger.info("Custom indicator calculated", indicator=name)
                return result

            # 2. 检查是否是内置指标
            if name in BUILTIN_INDICATORS:
                indicator_func = BUILTIN_INDICATORS[name]
                
                # 准备数据
                prepared_data = self._prepare_indicator_data(name, data, **kwargs)
                
                # 执行计算（在线程池中执行同步函数）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: indicator_func(**prepared_data, **kwargs)
                )
                
                # 转换结果为 DataFrame（如果是 dict）
                if isinstance(result, dict):
                    result = pd.DataFrame(result)
                
                logger.info("Built-in indicator calculated", indicator=name)
                return result

            # 3. 指标未找到
            raise IndicatorNotFoundError(name)

        except IndicatorNotFoundError:
            raise
        except IndicatorCalculationError:
            raise
        except Exception as e:
            logger.error(
                "Indicator calculation failed",
                indicator=name,
                error=str(e),
                exc_info=True,
            )
            raise IndicatorCalculationError(name, str(e)) from e

    def _prepare_indicator_data(
        self,
        name: str,
        data: pd.DataFrame,
        **kwargs,
    ) -> dict[str, Any]:
        """
        准备指标计算所需的数据

        根据指标名称自动提取对应的列数据

        Args:
            name: 指标名称
            data: 输入DataFrame
            **kwargs: 额外参数

        Returns:
            指标函数所需的参数字典

        Raises:
            IndicatorCalculationError: 缺少必要列
        """
        required_cols = INDICATOR_REQUIRED_COLUMNS.get(name, [])
        
        # 检查列是否存在
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise IndicatorCalculationError(
                name,
                f"Missing required columns: {missing}. Available: {list(data.columns)}",
            )
        
        # 准备参数
        prepared: dict[str, Any] = {}
        
        # 根据指标类型准备数据
        if name in ["sma", "ema", "rsi", "momentum", "rate_of_change"]:
            # 一元指标：只需 close
            prepared["data" if name in ["sma", "ema"] else "close_prices"] = data["close"]
        
        elif name in ["macd", "bollinger_bands"]:
            # 复合指标：只需 close
            prepared["close_prices"] = data["close"]
        
        elif name in ["atr", "stochastic_oscillator", "williams_r"]:
            # 三元指标：需要 high/low/close
            prepared["high_prices"] = data["high"]
            prepared["low_prices"] = data["low"]
            prepared["close_prices"] = data["close"]
        
        elif name == "obv":
            # OBV：需要 close 和 volume
            prepared["close_prices"] = data["close"]
            prepared["volume"] = data["volume"]
        
        elif name == "money_flow_index":
            # MFI：需要 high/low/close/volume
            prepared["high_prices"] = data["high"]
            prepared["low_prices"] = data["low"]
            prepared["close_prices"] = data["close"]
            prepared["volume"] = data["volume"]
        
        else:
            # 默认：尝试将所有列作为参数传递
            # 检查函数签名，匹配列名
            indicator_func = BUILTIN_INDICATORS[name]
            sig = signature(indicator_func)
            
            for param_name in sig.parameters:
                if param_name in data.columns:
                    prepared[param_name] = data[param_name]
        
        return prepared

    async def calculate_indicators(
        self,
        data: pd.DataFrame,
        indicator_names: list[str],
        params: dict[str, dict] | None = None,
    ) -> dict[str, pd.Series | pd.DataFrame]:
        """
        批量计算多个指标

        Args:
            data: 输入数据
            indicator_names: 指标名称列表
            params: 每个指标的参数 {'rsi': {'period': 14}, ...}

        Returns:
            {指标名: 计算结果}

        Example:
            >>> results = await core.calculate_indicators(
            ...     df,
            ...     ['rsi', 'macd', 'sma'],
            ...     {'rsi': {'period': 14}, 'sma': {'period': 20}}
            ... )
        """
        params = params or {}
        results: dict[str, pd.Series | pd.DataFrame] = {}

        logger.info(
            "Batch calculating indicators",
            indicators=indicator_names,
            params=params,
        )

        # 并发计算所有指标
        tasks = []
        for name in indicator_names:
            indicator_params = params.get(name, {})
            task = self.calculate_indicator(name, data, **indicator_params)
            tasks.append((name, task))

        # 等待所有任务完成
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                logger.debug("Indicator calculated", indicator=name)
            except (IndicatorNotFoundError, IndicatorCalculationError) as e:
                logger.warning(
                    "Indicator calculation skipped",
                    indicator=name,
                    error=str(e),
                )
                # 不中断整个批量计算，跳过失败的指标
                continue

        logger.info(
            "Batch calculation complete",
            total=len(indicator_names),
            success=len(results),
            failed=len(indicator_names) - len(results),
        )

        return results

    # ========================================================================
    # AI辅助分析
    # ========================================================================

    async def analyze_with_ai(
        self,
        data: dict[str, Any],
        task: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        使用AI进行分析

        Args:
            data: 待分析数据
            task: 分析任务描述
            provider: AI提供商名称（可选，默认使用第一个注册的提供商）
            model: 模型名称（可选）

        Returns:
            分析结果

        Raises:
            AIProviderNotFoundError: AI提供商未找到
            AIAnalysisError: AI分析失败

        Example:
            >>> result = await core.analyze_with_ai(
            ...     {'rsi': 70, 'macd': {'macd': 0.5}},
            ...     '分析当前市场状态并给出交易建议'
            ... )
        """
        logger.info(
            "Starting AI analysis",
            provider=provider,
            model=model,
            task=task,
        )

        try:
            # 选择AI提供商
            ai_provider = self._select_ai_provider(provider)
            
            if ai_provider is None:
                raise AIProviderNotFoundError(
                    provider or "default"
                )

            logger.debug(
                "Using AI provider",
                provider=ai_provider.name,
                model=model,
            )

            # 调用AI进行分析
            result = await ai_provider.analyze(
                data=data,
                task=task,
                model=model,
            )

            logger.info(
                "AI analysis complete",
                provider=ai_provider.name,
                model=model,
            )

            return result

        except AIProviderNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "AI analysis failed",
                provider=provider,
                model=model,
                error=str(e),
                exc_info=True,
            )
            raise AIAnalysisError(str(e)) from e

    def _select_ai_provider(
        self,
        name: str | None,
    ) -> AIProviderInterface | None:
        """
        选择AI提供商

        Args:
            name: 提供商名称（可选）

        Returns:
            AI提供商实例
        """
        if name:
            return self._ai_providers.get(name)
        
        # 默认选择第一个注册的提供商
        if self._ai_providers:
            return next(iter(self._ai_providers.values()))
        
        return None

    # ========================================================================
    # 健康检查
    # ========================================================================

    async def health_check(self) -> dict[str, Any]:
        """
        执行健康检查

        Returns:
            健康状态信息
        """
        logger.info("Running health check")

        status: dict[str, Any] = {
            "status": "healthy",
            "indicators": {
                "custom": len(self._indicators),
                "builtin": len(BUILTIN_INDICATORS),
            },
            "ai_providers": {},
        }

        # 检查AI提供商健康状态
        for name, provider in self._ai_providers.items():
            try:
                is_healthy = await provider.health_check()
                provider_status: dict[str, Any] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "models": provider.supported_models,
                }
                status["ai_providers"][name] = provider_status
            except Exception as e:
                error_status: dict[str, Any] = {
                    "status": "error",
                    "error": str(e),
                }
                status["ai_providers"][name] = error_status
                status["status"] = "degraded"

        logger.info("Health check complete", status=status["status"])
        return status

    # ========================================================================
    # 工具方法
    # ========================================================================

    def get_indicator_info(self, name: str) -> dict[str, Any] | None:
        """
        获取指标信息

        Args:
            name: 指标名称

        Returns:
            指标信息字典
        """
        # 检查自定义指标
        if name in self._indicators:
            indicator = self._indicators[name]
            required_cols: list[str] = list(indicator.required_columns)
            return {
                "name": indicator.name,
                "type": "custom",
                "description": indicator.description,
                "params": indicator.params,
                "required_columns": required_cols,
            }

        # 检查内置指标
        if name in BUILTIN_INDICATORS:
            builtin_required_cols: list[str] = list(INDICATOR_REQUIRED_COLUMNS.get(name, []))
            return {
                "name": name,
                "type": "builtin",
                "description": f"Built-in indicator: {name}",
                "params": {},  # 内置指标的参数由函数签名决定
                "required_columns": builtin_required_cols,
            }

        return None
