"""
分析任务

异步分析任务定义
"""

from typing import Any

from app.analysis.analyst import Analyst
from app.analysis.system import SystemAnalyzer
from app.analysis.trader import Trader
from app.models.analysis import AnalysisMode, AnalysisResult, AnalysisType
from app.report.generator import get_report_generator
from app.report.storage import get_report_storage
from app.tasks.celery_app import celery_app
from app.tasks.dead_letter import send_to_dead_letter_queue
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    retry_backoff=60,
    retry_jitter=True,
)
def async_analyze(
    self: Any,
    stock_code: str,
    analysis_type: str = "both",
    mode: str = "algorithm",
) -> dict[str, Any]:
    """
    异步分析任务

    Args:
        self: Celery 任务实例
        stock_code: 股票代码
        analysis_type: 分析类型 (long/short/both)
        mode: 分析模式 (algorithm/ai_enhanced)

    Returns:
        分析结果
    """
    logger.info(
        "async_analyze_started",
        task_id=self.request.id,
        stock_code=stock_code,
        analysis_type=analysis_type,
        mode=mode,
    )

    try:
        # 创建数据获取和分析实例
        import asyncio
        from datetime import date, timedelta

        from app.core.exceptions import DataSourceError, DataSourceTimeoutError
        from app.data.data_fetcher import DataFetcher

        async def _analyze():
            fetcher = DataFetcher()
            analyst = Analyst()
            trader = Trader()
            system = SystemAnalyzer()

            # analysis_type 已在 system.analyze() 中处理
            # mode 参数用于后续的 AI 增强分析 (待实现)

            # 1. 并行获取数据(性能优化)
            end_date = date.today()
            start_date = end_date - timedelta(days=settings.analysis_days)

            stock_info_task = fetcher.get_stock_info(stock_code)
            quotes_task = fetcher.get_daily_quotes(stock_code, start_date, end_date)
            financial_task = fetcher.get_financial_data(stock_code)

            stock_info, quotes, financial = await asyncio.gather(
                stock_info_task,
                quotes_task,
                financial_task,
            )

            # 2. 执行三阶段分析
            # 执行分析师和交易员分析（结果用于日志和监控）
            _ = await analyst.analyze(stock_info, quotes, financial)
            _ = await trader.analyze(stock_info, quotes, financial)
            # 执行系统综合分析
            analysis_result = await system.analyze(
                stock_info=stock_info,
                quotes=quotes,
                financial=financial,
                analysis_type=analysis_type,
            )

            return analysis_result

        analysis_result = asyncio.run(_analyze())

        # 从结果中提取信息
        total_score = analysis_result.scores.get("total", 50)
        recommendation = analysis_result.details.get("recommendation", "持有")
        confidence = analysis_result.details.get("confidence", 60)

        # 生成分析ID
        analysis_id = f"ana-{stock_code}-{date.today().strftime('%Y%m%d%H%M%S')}"

        logger.info(
            "async_analyze_completed",
            task_id=self.request.id,
            stock_code=stock_code,
            total_score=total_score,
            recommendation=recommendation,
        )

        return {
            "status": "success",
            "analysis_id": analysis_id,
            "stock_code": stock_code,
            "total_score": total_score,
            "recommendation": recommendation,
            "confidence": confidence,
        }

    except DataSourceTimeoutError as e:
        # 数据源超时,指数退避重试
        logger.warning(
            "data_source_timeout_retrying",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
            retry_count=self.request.retries,
        )

        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue.delay(
                task_name="async_analyze",
                task_id=str(self.request.id),
                args={
                    "stock_code": stock_code,
                    "analysis_type": analysis_type,
                    "mode": mode,
                },
                error=str(e),
            )
            raise

        # 指数退避重试:60s * 2^retry_count
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    except DataSourceError as e:
        # 数据源错误,短暂延迟后重试
        logger.warning(
            "data_source_error_retrying",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
            retry_count=self.request.retries,
        )

        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue.delay(
                task_name="async_analyze",
                task_id=str(self.request.id),
                args={
                    "stock_code": stock_code,
                    "analysis_type": analysis_type,
                    "mode": mode,
                },
                error=str(e),
            )
            raise

        raise self.retry(exc=e, countdown=30)

    except Exception as e:
        # 其他错误,不重试,直接发送到死信队列
        logger.error(
            "async_analyze_failed_no_retry",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
        )

        send_to_dead_letter_queue.delay(
            task_name="async_analyze",
            task_id=str(self.request.id),
            args={
                "stock_code": stock_code,
                "analysis_type": analysis_type,
                "mode": mode,
            },
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
    max_retries=3,
    retry_backoff=60,
)
def async_analyze_and_report(
    self: Any,
    stock_code: str,
    analysis_type: str = "both",
    mode: str = "algorithm",
) -> dict[str, Any]:
    """
    异步分析并生成报告

    Args:
        self: Celery 任务实例
        stock_code: 股票代码
        analysis_type: 分析类型
        mode: 分析模式

    Returns:
        分析和报告结果
    """
    logger.info(
        "async_analyze_and_report_started",
        task_id=self.request.id,
        stock_code=stock_code,
    )

    try:
        # 执行分析（同步调用 async_analyze 的逻辑）
        import asyncio
        from datetime import date, timedelta

        from app.core.exceptions import DataSourceError, DataSourceTimeoutError
        from app.data.data_fetcher import DataFetcher

        async def _analyze():
            fetcher = DataFetcher()
            analyst = Analyst()
            trader = Trader()
            system = SystemAnalyzer()

            # analysis_type 已在 system.analyze() 中处理
            # mode 参数用于后续的 AI 增强分析 (待实现)

            # 并行获取数据
            end_date = date.today()
            start_date = end_date - timedelta(days=settings.analysis_days)

            stock_info_task = fetcher.get_stock_info(stock_code)
            quotes_task = fetcher.get_daily_quotes(stock_code, start_date, end_date)
            financial_task = fetcher.get_financial_data(stock_code)

            stock_info, quotes, financial = await asyncio.gather(
                stock_info_task,
                quotes_task,
                financial_task,
            )

            # 执行分析
            # 执行分析师和交易员分析（结果用于日志和监控）
            _ = await analyst.analyze(stock_info, quotes, financial)
            _ = await trader.analyze(stock_info, quotes, financial)
            # 执行系统综合分析
            analysis_result = await system.analyze(
                stock_info=stock_info,
                quotes=quotes,
                financial=financial,
                analysis_type=analysis_type,
            )

            return analysis_result, stock_info

        analysis_result, stock_info = asyncio.run(_analyze())

        # 生成分析ID
        analysis_id = f"ana-{stock_code}-{date.today().strftime('%Y%m%d%H%M%S')}"

        # 生成报告
        generator = get_report_generator()
        report_content = generator.generate(analysis_result)

        # 保存报告
        storage = get_report_storage()
        storage.save(
            report_id=report_content.report_id,
            content=generator._generate_fallback_html(report_content.analysis_data),
            stock_code=stock_code,
            analysis_id=analysis_id,
            stock_name=stock_info.name,
        )

        logger.info(
            "async_analyze_and_report_completed",
            task_id=self.request.id,
            stock_code=stock_code,
            report_id=report_content.report_id,
        )

        return {
            "status": "success",
            "analysis_id": analysis_id,
            "report_id": report_content.report_id,
            "stock_code": stock_code,
        }

    except DataSourceTimeoutError as e:
        # 数据源超时，指数退避重试
        logger.warning(
            "data_source_timeout_retrying",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
            retry_count=self.request.retries,
        )

        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue.delay(
                task_name="async_analyze_and_report",
                task_id=str(self.request.id),
                args={"stock_code": stock_code},
                error=str(e),
            )
            raise

        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    except DataSourceError as e:
        # 数据源错误，短暂延迟后重试
        logger.warning(
            "data_source_error_retrying",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
            retry_count=self.request.retries,
        )

        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue.delay(
                task_name="async_analyze_and_report",
                task_id=str(self.request.id),
                args={"stock_code": stock_code},
                error=str(e),
            )
            raise

        raise self.retry(exc=e, countdown=30)

    except Exception as e:
        # 其他错误，不重试
        logger.error(
            "async_analyze_and_report_failed_no_retry",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
        )

        send_to_dead_letter_queue.delay(
            task_name="async_analyze_and_report",
            task_id=str(self.request.id),
            args={"stock_code": stock_code},
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
    max_retries=2,
)
def batch_analyze(
    self: Any,
    stock_codes: list[str],
    analysis_type: str = "both",
) -> dict[str, Any]:
    """
    批量分析任务

    Args:
        self: Celery 任务实例
        stock_codes: 股票代码列表
        analysis_type: 分析类型

    Returns:
        批量分析结果
    """
    logger.info(
        "batch_analyze_started",
        task_id=self.request.id,
        count=len(stock_codes),
    )

    results = []
    errors = []

    for stock_code in stock_codes:
        try:
            # 为每个股票启动单独的分析任务
            result = async_analyze.delay(stock_code, analysis_type)
            results.append({"stock_code": stock_code, "task_id": result.id})
        except Exception as e:
            errors.append({"stock_code": stock_code, "error": str(e)})

    return {
        "status": "success" if not errors else "partial",
        "total": len(stock_codes),
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
