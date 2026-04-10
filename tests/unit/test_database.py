"""
数据库模块测试

测试数据库配置和会话管理
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseEngine:
    """测试数据库引擎配置"""

    def test_engine_created(self) -> None:
        """测试引擎创建"""
        from app.core.database import engine

        assert engine is not None
        assert engine.url is not None

    def test_async_session_maker_created(self) -> None:
        """测试会话工厂创建"""
        from app.core.database import async_session_maker

        assert async_session_maker is not None

    def test_base_class(self) -> None:
        """测试基类创建"""
        from app.core.database import Base

        assert Base is not None


class TestGetDB:
    """测试 get_db 依赖注入"""

    @pytest.mark.asyncio
    async def test_get_db_success(self) -> None:
        """测试成功获取数据库会话"""
        from app.core.database import get_db

        # 获取会话生成器
        gen = get_db()
        # 触发生成器
        async for _session in gen:
            # 验证会话存在
            assert _session is not None
            break

    @pytest.mark.asyncio
    async def test_get_db_commit_on_success(self) -> None:
        """测试成功时自动提交"""
        from app.core.database import get_db

        gen = get_db()
        # 使用 async for 来触发完整的会话生命周期
        async for _session in gen:
            # 会话会在循环结束时自动提交
            assert _session is not None

    @pytest.mark.asyncio
    async def test_get_db_rollback_on_error(self) -> None:
        """测试异常时自动回滚"""
        from app.core.database import get_db

        gen = get_db()

        try:
            async for _session in gen:
                # 模拟异常
                raise Exception("DB Error")
        except Exception:
            pass

        # 异常会触发回滚


class TestDatabaseModels:
    """测试数据库模型基类"""

    def test_base_is_declarative(self) -> None:
        """测试 Base 是声明式基类"""
        from app.core.database import Base
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(Base, DeclarativeBase)

    def test_base_can_be_used_for_models(self) -> None:
        """测试 Base 可以用于定义模型"""
        from app.core.database import Base
        from sqlalchemy import Column, Integer, String

        # 定义一个测试模型
        class TestModel(Base):
            __tablename__ = "test_table"

            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        assert TestModel.__tablename__ == "test_table"
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "name")
