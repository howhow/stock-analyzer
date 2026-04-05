"""缓存管理测试 - 简化版"""

import pytest
from app.core.cache import CacheManager


class TestCacheManager:
    """缓存管理器测试"""

    def test_init(self):
        """测试初始化"""
        cache = CacheManager(redis_url="", max_local_size=100)
        assert cache.max_local_size == 100
        assert cache.default_ttl == 1800

    @pytest.mark.asyncio
    async def test_set_get(self):
        """测试设置和获取"""
        cache = CacheManager(redis_url="")
        # 同步设置
        cache.set("key1", "value1", ttl=60)
        # 验证本地缓存已设置
        assert "key1" in cache._local_cache

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = CacheManager(redis_url="")
        result = await cache.get("nonexistent")
        assert result is None
