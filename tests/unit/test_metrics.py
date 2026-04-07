"""
监控指标测试
"""

import pytest

from app.monitoring.metrics import (
    get_content_type,
    get_metrics,
    record_ai_call,
    record_analysis,
    record_cache_hit,
    record_cache_miss,
    record_celery_task,
    record_data_source_request,
    record_http_request,
    record_rate_limit,
    record_report_generation,
    update_cache_metrics,
    update_circuit_breaker_state,
    update_data_source_availability,
)


class TestMetrics:
    """监控指标测试"""

    def test_get_metrics(self) -> None:
        """测试获取指标"""
        metrics = get_metrics()
        assert metrics is not None
        assert isinstance(metrics, bytes)

    def test_get_content_type(self) -> None:
        """测试获取内容类型"""
        content_type = get_content_type()
        assert "text/plain" in content_type

    def test_record_http_request(self) -> None:
        """测试记录 HTTP 请求"""
        record_http_request(
            method="GET",
            endpoint="/api/v1/analysis",
            status=200,
            duration=0.5,
        )

    def test_record_analysis(self) -> None:
        """测试记录分析"""
        record_analysis(
            analysis_type="long",
            mode="algorithm",
            status="success",
            duration=2.5,
            score=3.5,
        )

    def test_record_cache_hit(self) -> None:
        """测试记录缓存命中"""
        record_cache_hit(cache_type="redis")

    def test_record_cache_miss(self) -> None:
        """测试记录缓存未命中"""
        record_cache_miss(cache_type="local")

    def test_update_cache_metrics(self) -> None:
        """测试更新缓存指标"""
        update_cache_metrics(
            cache_type="redis",
            size=1024 * 1024,
            items=100,
        )

    def test_record_data_source_request(self) -> None:
        """测试记录数据源请求"""
        record_data_source_request(
            source="tushare",
            status="success",
            latency=0.3,
        )

    def test_update_data_source_availability(self) -> None:
        """测试更新数据源可用性"""
        update_data_source_availability(source="tushare", available=True)
        update_data_source_availability(source="akshare", available=False)

    def test_update_circuit_breaker_state(self) -> None:
        """测试更新熔断器状态"""
        update_circuit_breaker_state(name="tushare", state=0)  # closed
        update_circuit_breaker_state(name="akshare", state=1)  # open

    def test_record_celery_task(self) -> None:
        """测试记录 Celery 任务"""
        record_celery_task(
            task_name="async_analyze",
            status="success",
            duration=5.0,
        )

    def test_record_report_generation(self) -> None:
        """测试记录报告生成"""
        record_report_generation(format_type="html", status="success")

    def test_record_rate_limit(self) -> None:
        """测试记录限流"""
        record_rate_limit(user_tier="free", endpoint="analyze")

    def test_record_ai_call(self) -> None:
        """测试记录 AI 调用"""
        record_ai_call(
            provider="openai",
            model="gpt-4",
            status="success",
            latency=2.0,
            cost=0.05,
        )

    def test_metrics_content(self) -> None:
        """测试指标内容"""
        # 记录一些指标
        record_http_request("GET", "/test", 200, 0.1)
        record_cache_hit("redis")

        # 获取指标
        metrics = get_metrics().decode("utf-8")

        # 验证包含预期的指标名称
        assert "http_requests_total" in metrics
        assert "cache_hits_total" in metrics
