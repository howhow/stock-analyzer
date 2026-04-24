"""
分析 API
"""

import asyncio
from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DataFetcherDep
from app.data.data_fetcher import DataFetcher
from app.models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    BatchAnalysisRequest,
    DimensionScores,
    Recommendation,
)
from app.utils.logger import get_logger
from app.utils.timer import timer
from config.settings import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["分析"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="单次股票分析",
    description="对单只股票进行技术面和基本面分析，返回投资建议",
)
async def analyze_stock(
    request: AnalysisRequest,
    fetcher: DataFetcherDep,
) -> AnalysisResponse:
    """
    单次股票分析

    Args:
        request: 分析请求
        fetcher: 数据获取器（依赖注入）

    Returns:
        分析结果
    """
    with timer("analyze_stock") as t:
        logger.info(
            "analysis_requested",
            stock_code=request.stock_code,
            analysis_type=request.analysis_type.value,
            mode=request.mode.value,
        )

        # 导入分析引擎
        from app.analysis.system import SystemAnalyzer
        from app.core.exceptions import DataSourceError, StockAnalyzerError

        try:
            # 1. 并行获取数据（性能优化：3x RTT → 1x RTT）
            end_date = date.today()
            start_date = end_date - timedelta(days=settings.analysis_days)

            stock_info_task = fetcher.get_stock_info(request.stock_code)
            quotes_task = fetcher.get_daily_quotes(
                request.stock_code, start_date, end_date
            )
            financial_task = fetcher.get_financial_data(request.stock_code)

            # 等待所有数据
            stock_info, quotes, financial = await asyncio.gather(
                stock_info_task,
                quotes_task,
                financial_task,
            )

            # 2. 执行分析
            system = SystemAnalyzer()
            result = await system.analyze(
                stock_info=stock_info,
                quotes=quotes,
                financial=financial,
                analysis_type=request.analysis_type.value,
            )

            # 3. 构建响应
            analysis_id = (
                f"ana-{request.stock_code}-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            # 从结果中提取评分和建议
            total_score = result.scores.get("total", 50)
            recommendation_str = result.details.get("recommendation", "持有")
            confidence = result.details.get("confidence", 60)

            # 转换推荐字符串为枚举
            recommendation_map = {
                "强烈买入": Recommendation.STRONG_BUY,
                "买入": Recommendation.BUY,
                "持有": Recommendation.HOLD,
                "卖出": Recommendation.SELL,
                "强烈卖出": Recommendation.STRONG_SELL,
            }
            recommendation = recommendation_map.get(
                recommendation_str, Recommendation.HOLD
            )

            # 从 trader 结果中提取维度评分
            trader_detail = result.details.get("trader", {})
            scores_data = trader_detail.get("scores", {})

            scores = DimensionScores(
                signal_strength=scores_data.get("signal_strength", 2.5),
                opportunity_quality=scores_data.get("opportunity_quality", 2.5),
                risk_level=scores_data.get("risk_level", 3.0),
            )

            response = AnalysisResponse(
                analysis_id=analysis_id,
                stock_code=request.stock_code,
                stock_name=stock_info.name,
                scores=scores,
                total_score=total_score,
                recommendation=recommendation,
                confidence=float(confidence),
            )

            logger.info(
                "analysis_completed",
                stock_code=request.stock_code,
                total_score=total_score,
                recommendation=recommendation.value,
                elapsed_ms=t["elapsed"],
            )

            return response

        except DataSourceError as e:
            logger.error(
                "data_source_error",
                stock_code=request.stock_code,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Data source unavailable: {str(e)}",
            )
        except StockAnalyzerError as e:
            logger.error(
                "analysis_error",
                stock_code=request.stock_code,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Analysis error: {str(e)}",
            )
        except Exception as e:
            logger.error(
                "unexpected_error",
                stock_code=request.stock_code,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


@router.post(
    "/batch-analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="批量股票分析",
    description="批量分析多只股票，异步处理",
)
async def batch_analyze(request: BatchAnalysisRequest) -> dict[str, str | int]:
    """
    批量股票分析（异步）

    Args:
        request: 批量分析请求

    Returns:
        任务ID列表
    """
    logger.info(
        "batch_analysis_requested",
        stock_count=len(request.stock_codes),
        analysis_type=request.analysis_type.value,
    )

    # 提交到 Celery 任务队列
    from app.tasks.analysis_tasks import batch_analyze as batch_analyze_task

    result = batch_analyze_task.delay(
        stock_codes=request.stock_codes,
        analysis_type=request.analysis_type.value,
    )

    return {
        "status": "accepted",
        "task_count": len(request.stock_codes),
        "task_id": result.id,
        "message": "Batch analysis tasks submitted",
    }


@router.get(
    "/{symbol}",
    response_model=AnalysisResponse,
    summary="快捷股票分析",
    description="通过URL路径参数快速分析单只股票，GET请求幂等且可缓存",
)
async def analyze_stock_by_symbol(
    symbol: str,
    fetcher: DataFetcherDep,
    analysis_type: str = "both",
    mode: str = "algorithm",
) -> AnalysisResponse:
    """
    快捷股票分析 - GET 接口

    Args:
        symbol: 股票代码（如 688981.SH）
        fetcher: 数据获取器（依赖注入）
        analysis_type: 分析类型（comprehensive/technical/fundamental）
        mode: 分析模式（realtime/historical）

    Returns:
        分析结果
    """
    from app.models import AnalysisType, AnalysisMode

    # 构建请求对象
    request = AnalysisRequest(
        stock_code=symbol,
        analysis_type=AnalysisType(analysis_type),
        mode=AnalysisMode(mode),
    )

    # 复用 POST 接口逻辑
    return await analyze_stock(request, fetcher)


@router.get(
    "/result/{analysis_id}",
    response_model=AnalysisResult,
    summary="获取分析结果",
)
async def get_analysis_result(analysis_id: str) -> AnalysisResult:
    """
    获取分析结果

    Args:
        analysis_id: 分析ID

    Returns:
        分析结果详情
    """
    logger.info("analysis_result_requested", analysis_id=analysis_id)

    # TODO: 从数据库或缓存获取结果
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Analysis result not found: {analysis_id}",
    )
