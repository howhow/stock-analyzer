"""
API 路由汇总
"""

from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.config import router as config_router
from app.api.v1.health import router as health_router
from app.api.v1.report import router as report_router
from app.api.v1.subscribe import router as subscribe_router

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health_router)
api_router.include_router(analysis_router, prefix="/v1")
api_router.include_router(subscribe_router, prefix="/v1")
api_router.include_router(report_router, prefix="/v1")
api_router.include_router(config_router, prefix="/v1")
