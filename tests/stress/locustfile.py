"""压力测试 locustfile"""

from locust import HttpUser, between, task


class APIUser(HttpUser):
    """API 压力测试用户"""

    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        """健康检查端点"""
        self.client.get("/api/v1/health")

    @task(2)
    def analyze_stock(self):
        """股票分析端点"""
        self.client.post(
            "/api/v1/analysis", json={"symbol": "600519.SH", "analysis_type": "dcf"}
        )
