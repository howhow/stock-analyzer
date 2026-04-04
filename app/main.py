"""
Stock Analyzer - 股票分析与交易机会识别系统

FastAPI 主入口
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.error_handler import register_exception_handlers
from app.utils.logger import get_logger, setup_logging
from config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理

    startup: 初始化资源
    shutdown: 清理资源
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        env=settings.app_env,
        debug=settings.app_debug,
    )

    # TODO: 初始化数据库连接池
    # TODO: 初始化 Redis 连接
    # TODO: 初始化数据源客户端

    yield

    # Shutdown
    logger.info("application_shutting_down")
    # TODO: 清理资源


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    Returns:
        配置好的 FastAPI 应用
    """
    app = FastAPI(
        title=settings.app_name,
        description="股票分析与交易机会识别系统 - 全AI自主股票分析系统",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: 生产环境限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册异常处理器
    register_exception_handlers(app)

    # 注册路由
    app.include_router(api_router, prefix="/api")

    # 根路径
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
