"""
分析 API 测试
"""

from fastapi.testclient import TestClient


def test_analyze_stock(client: TestClient):
    """测试单次分析接口"""
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "stock_code": "600519.SH",
            "analysis_type": "long",
            "mode": "algorithm",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "stock_code" in data
    assert "total_score" in data


def test_analyze_stock_invalid_code(client: TestClient):
    """测试无效股票代码 - 目前返回 mock 数据"""
    # NOTE: 当前是 mock 实现，不验证股票代码
    # TODO: 实现真实分析逻辑后添加验证
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "stock_code": "INVALID",
            "analysis_type": "long",
        },
    )
    # Mock 阶段暂时返回 200
    assert response.status_code == 200


def test_batch_analyze(client: TestClient):
    """测试批量分析接口"""
    response = client.post(
        "/api/v1/analysis/batch-analyze",
        json={
            "stock_codes": ["600519.SH", "000001.SZ"],
            "analysis_type": "both",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"


def test_get_analysis_result_not_found(client: TestClient):
    """测试获取不存在的分析结果"""
    response = client.get("/api/v1/analysis/result/nonexistent-id")
    assert response.status_code == 404
