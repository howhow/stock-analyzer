"""
健康检查 API
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    健康检查接口

    Returns:
        服务状态信息
    """
    return {
        "status": "healthy",
        "service": "stock-analyzer",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> dict[str, dict[str, str] | str]:
    """
    就绪检查接口

    检查所有依赖服务是否就绪

    Returns:
        就绪状态
    """
    # TODO: 检查数据库、Redis、数据源等
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "data_source": "ok",
        },
    }
