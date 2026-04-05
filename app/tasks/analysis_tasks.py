"""
分析任务

异步分析任务定义
"""

from typing import Any

from app.analysis.analyst import Analyst
from app.analysis.trader import Trader
from app.analysis.system import SystemAnalyzer
from app.models.analysis import AnalysisType, AnalysisMode, AnalysisResult
from app.report.generator import get_report_generator
from app.report.storage import get_report_storage
from app.tasks.celery_app import celery_app
from app.tasks.dead_letter import send_to_dead_letter_queue
from app.utils.logger import get_logger

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
        # 创建分析师实例
        analyst = Analyst()
        trader = Trader()
        system = SystemAnalyzer()

        # 执行分析
        analysis_type_enum = AnalysisType(analysis_type)
        mode_enum = AnalysisMode(mode)

        # 第一阶段：分析师分析
        analyst_report = analyst.analyze(stock_code, analysis_type_enum)

        # 第二阶段：交易员分析
        trader_signal = trader.analyze(stock_code, analysis_type_enum, analyst_report)

        # 第三阶段：系统综合
        analysis_result = system.synthesize(
            stock_code=stock_code,
            analyst_report=analyst_report,
            trader_signal=trader_signal,
            analysis_type=analysis_type_enum,
            mode=mode_enum,
        )

        logger.info(
            "async_analyze_completed",
            task_id=self.request.id,
            stock_code=stock_code,
            total_score=analysis_result.analyst_report.total_score,
        )

        return {
            "status": "success",
            "analysis_id": analysis_result.analysis_id,
            "stock_code": stock_code,
            "total_score": analysis_result.analyst_report.total_score,
            "recommendation": analysis_result.trader_signal.recommendation.value,
        }

    except Exception as e:
        logger.error(
            "async_analyze_failed",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
            retry_count=self.request.retries,
        )

        # 达到最大重试次数，发送到死信队列
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

        # 重试
        raise self.retry(exc=e)


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
        analyst = Analyst()
        trader = Trader()
        system = SystemAnalyzer()

        analysis_type_enum = AnalysisType(analysis_type)
        mode_enum = AnalysisMode(mode)

        analyst_report = analyst.analyze(stock_code, analysis_type_enum)
        trader_signal = trader.analyze(stock_code, analysis_type_enum, analyst_report)
        analysis_result = system.synthesize(
            stock_code=stock_code,
            analyst_report=analyst_report,
            trader_signal=trader_signal,
            analysis_type=analysis_type_enum,
            mode=mode_enum,
        )

        # 生成报告
        generator = get_report_generator()
        report_content = generator.generate(analysis_result)

        # 保存报告
        storage = get_report_storage()
        storage.save(
            report_id=report_content.report_id,
            content=generator._generate_fallback_html(report_content.analysis_data),
            stock_code=stock_code,
            analysis_id=analysis_result.analysis_id,
            stock_name=analysis_result.stock_name,
        )

        logger.info(
            "async_analyze_and_report_completed",
            task_id=self.request.id,
            stock_code=stock_code,
            report_id=report_content.report_id,
        )

        return {
            "status": "success",
            "analysis_id": analysis_result.analysis_id,
            "report_id": report_content.report_id,
            "stock_code": stock_code,
        }

    except Exception as e:
        logger.error(
            "async_analyze_and_report_failed",
            task_id=self.request.id,
            stock_code=stock_code,
            error=str(e),
        )

        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue.delay(
                task_name="async_analyze_and_report",
                task_id=str(self.request.id),
                args={"stock_code": stock_code},
                error=str(e),
            )
            raise

        raise self.retry(exc=e)


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
