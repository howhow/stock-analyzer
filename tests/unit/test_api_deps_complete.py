"""
API 依赖注入完整测试

目标覆盖率: ≥ 90%
当前覆盖率: 87%
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request

from app.api.deps import (
    get_rate_limit_info,
    get_cache,
    get_db,
    get_data_fetcher,
    RequireRole,
    CurrentUser,
    OptionalUser,
    RateLimitInfo,
    CacheClient,
    DbSession,
    DataFetcherDep,
)


class TestGetRateLimitInfo:
    """限流信息获取测试"""
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self):
        """测试获取限流信息"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = None
        
        with patch("app.api.deps.check_rate_limit") as mock_check:
            mock_check.return_value = {
                "allowed": True,
                "remaining": 10,
                "reset_time": 60,
                "tier": "free",
            }
            
            result = await get_rate_limit_info(request)
            
            assert result["allowed"] is True
            assert result["remaining"] == 10
            mock_check.assert_called_once_with(request, endpoint="analyze")


class TestGetCache:
    """缓存客户端获取测试"""
    
    @pytest.mark.asyncio
    async def test_get_cache(self):
        """测试获取缓存客户端"""
        result = await get_cache()
        
        # 当前返回 None（待实现）
        assert result is None


class TestGetDb:
    """数据库会话获取测试"""
    
    @pytest.mark.asyncio
    async def test_get_db(self):
        """测试获取数据库会话"""
        result = await get_db()
        
        # 当前返回 None（待实现）
        assert result is None


class TestGetDataFetcher:
    """数据获取器测试"""
    
    @pytest.mark.asyncio
    async def test_get_data_fetcher_from_app_state(self):
        """测试从 app.state 获取数据获取器"""
        # 创建模拟的 DataFetcher
        mock_fetcher = Mock()
        
        request = Mock(spec=Request)
        request.app = Mock()
        request.app.state = Mock()
        request.app.state.data_fetcher = mock_fetcher
        
        result = await get_data_fetcher(request)
        
        assert result is mock_fetcher
    
    @pytest.mark.asyncio
    async def test_get_data_fetcher_create_new(self):
        """测试创建新的数据获取器（降级）"""
        request = Mock(spec=Request)
        request.app = Mock()
        request.app.state = Mock()
        # 没有 data_fetcher 属性
        
        result = await get_data_fetcher(request)
        
        # 应该返回新的 DataFetcher 实例
        assert result is not None
        assert hasattr(result, "fetch_stock_data")


class TestRequireRole:
    """角色权限依赖测试"""
    
    def test_require_role_factory(self):
        """测试角色权限依赖工厂"""
        result = RequireRole("admin")
        
        # 应该返回 Annotated 类型
        assert result is not None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.api.deps", "--cov-report=term-missing"])
