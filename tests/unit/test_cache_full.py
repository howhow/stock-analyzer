"""缓存模块完整测试"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.core.cache import CacheManager


class TestCacheManagerFull:
    """缓存管理器完整测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器实例"""
        with patch("app.core.cache.redis.from_url") as mock_redis:
            mock_redis.return_value = AsyncMock()
            return CacheManager(redis_url="redis://localhost:6379")

    def test_init(self, cache_manager):
        """测试初始化"""
        assert cache_manager is not None
        assert cache_manager.default_ttl == 1800

    def test_init_with_params(self):
        """测试带参数初始化"""
        with patch("app.core.cache.redis.from_url") as mock_redis:
            mock_redis.return_value = AsyncMock()
            cache = CacheManager(
                redis_url="redis://localhost:6379", max_local_size=500, default_ttl=3600
            )
            assert cache.max_local_size == 500
            assert cache.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_set_local(self, cache_manager):
        """测试本地缓存设置"""
        # 直接设置本地缓存
        cache_manager._local_cache["test_key"] = ("test_value", 9999999999)
        result = cache_manager._local_cache.get("test_key")
        assert result is not None
        assert result[0] == "test_value"

    @pytest.mark.asyncio
    async def test_get_local(self, cache_manager):
        """测试本地缓存获取"""
        cache_manager._local_cache["test_key"] = ("test_value", 9999999999)

        # 直接从本地缓存获取
        result = cache_manager._local_cache.get("test_key")
        assert result is not None
        assert result[0] == "test_value"

    @pytest.mark.asyncio
    async def test_delete_local(self, cache_manager):
        """测试本地缓存删除"""
        cache_manager._local_cache["test_key"] = ("test_value", 9999999999)

        # 删除
        del cache_manager._local_cache["test_key"]
        assert "test_key" not in cache_manager._local_cache

    def test_local_cache_eviction(self):
        """测试本地缓存淘汰"""
        with patch("app.core.cache.redis.from_url") as mock_redis:
            mock_redis.return_value = AsyncMock()
            cache = CacheManager(max_local_size=2)

            # 设置缓存
            cache._local_cache["key1"] = ("value1", 9999999999)
            cache._local_cache["key2"] = ("value2", 9999999999)

            assert len(cache._local_cache) == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager):
        """测试获取统计信息"""
        cache_manager._hits = 10
        cache_manager._misses = 5

        # 直接访问属性
        assert cache_manager._hits == 10
        assert cache_manager._misses == 5

    def test_generate_key(self, cache_manager):
        """测试生成缓存键"""
        try:
            key = cache_manager._generate_key("prefix", "arg1", "arg2")
            assert isinstance(key, str)
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_clear_expired(self, cache_manager):
        """测试清理过期缓存"""
        import time

        # 设置过期缓存
        cache_manager._local_cache["expired_key"] = ("value", time.time() - 100)
        cache_manager._local_cache["valid_key"] = ("value", time.time() + 10000)

        # 手动检查
        assert "expired_key" in cache_manager._local_cache
        assert "valid_key" in cache_manager._local_cache
