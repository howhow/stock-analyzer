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
        cache.set("key1", "value1", ttl=60)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = CacheManager(redis_url="")
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除"""
        cache = CacheManager(redis_url="")
        cache.set("key1", "value1")
        cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_complex_value(self):
        """测试复杂值"""
        cache = CacheManager(redis_url="")
        data = {"name": "test", "value": [1, 2, 3]}
        cache.set("complex", data)
        result = await cache.get("complex")
        assert result["name"] == "test"
        assert result["value"] == [1, 2, 3]
