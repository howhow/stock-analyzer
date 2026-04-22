"""
监控模块测试

测试监控指标占位模块。
"""

from app.monitoring import (
    get_metrics,
    record_analysis,
    record_cache_hit,
    record_cache_miss,
    record_http_request,
)


class TestMonitoringStubs:
    """测试监控占位函数"""

    def test_record_http_request(self):
        """测试 HTTP 请求记录占位符"""
        record_http_request("GET", "/api/v1/stocks", 200, 0.1)
        # 占位符不执行任何操作，不应抛出异常

    def test_record_analysis(self):
        """测试分析记录占位符"""
        record_analysis("600519.SH", "success", 1.5)
        # 占位符不执行任何操作，不应抛出异常

    def test_record_cache_hit(self):
        """测试缓存命中记录占位符"""
        record_cache_hit("stock_info_600519")
        # 占位符不执行任何操作，不应抛出异常

    def test_record_cache_miss(self):
        """测试缓存未命中记录占位符"""
        record_cache_miss("stock_info_600519")
        # 占位符不执行任何操作，不应抛出异常

    def test_get_metrics(self):
        """测试获取指标占位符"""
        result = get_metrics()
        assert result == b""

    def test_record_http_request_with_kwargs(self):
        """测试 HTTP 记录带关键字参数"""
        record_http_request(
            method="POST", path="/api/v1/analyze", status=201, duration=0.2
        )

    def test_record_analysis_with_kwargs(self):
        """测试分析记录带关键字参数"""
        record_analysis(stock_code="000001.SZ", status="failed", duration=2.0)
