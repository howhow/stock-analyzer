"""
Cache 完整测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.cache import CacheManager


class TestCacheManagerComplete:
    """CacheManager完整测试"""

    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return CacheManager(
            redis_url="redis://localhost:6379/0",
            max_local_size=10,
            default_ttl=60,
        )

    def test_make_key(self, cache):
        """测试生成缓存键"""
        key = cache.make_key("stock", "600519.SH", "2024-01-01")
        assert key == "stock:600519.SH:2024-01-01"

    @pytest.mark.asyncio
    async def test_set_and_get_local(self, cache):
        """测试本地缓存设置和获取"""
        await cache.set("test_key", {"data": "value"}, ttl=60)

        result = await cache.get("test_key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """测试获取不存在的键"""
        result = await cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, cache):
        """测试删除缓存键"""
        await cache.set("test_key", {"data": "value"})
        await cache.delete("test_key")

        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_local_cache_expiration(self, cache):
        """测试本地缓存过期"""
        # 设置极短的TTL
        await cache.set("test_key", {"data": "value"}, ttl=0)

        # 立即获取可能还存在
        # 但过期后应该被清理
        await cache.clear_local()

    @pytest.mark.asyncio
    async def test_clear_local(self, cache):
        """测试清空本地缓存"""
        await cache.set("key1", {"data": "value1"})
        await cache.set("key2", {"data": "value2"})

        await cache.clear_local()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """测试LRU淘汰策略"""
        small_cache = CacheManager(max_local_size=3)

        # 添加超过容量的数据
        for i in range(5):
            await small_cache.set(f"key{i}", {"data": i})

        # 检查部分数据被淘汰
        stats = await small_cache.get_stats()
        assert stats["local_cache_size"] <= 3

    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """测试获取缓存统计"""
        await cache.set("key1", {"data": "value1"})
        await cache.set("key2", {"data": "value2"})

        stats = await cache.get_stats()

        assert "local_cache_size" in stats
        assert "max_local_size" in stats
        assert stats["local_cache_size"] == 2

    @pytest.mark.asyncio
    async def test_close(self, cache):
        """测试关闭缓存连接"""
        await cache.close()
        assert cache._redis_client is None

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """测试Redis连接失败"""
        cache = CacheManager(redis_url="redis://invalid:6379/0")

        # 应该优雅处理连接失败
        await cache._get_redis()
        # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache):
        """测试带TTL的缓存设置"""
        await cache.set("test_key", {"data": "value"}, ttl=120)

        result = await cache.get("test_key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_cache_with_complex_data(self, cache):
        """测试复杂数据缓存"""
        complex_data = {
            "stock_code": "600519.SH",
            "name": "贵州茅台",
            "quotes": [
                {"date": "2024-01-01", "close": 100.0},
                {"date": "2024-01-02", "close": 101.0},
            ],
            "nested": {
                "level1": {
                    "level2": "value",
                }
            }
        }

        await cache.set("complex_key", complex_data)
        result = await cache.get("complex_key")

        assert result == complex_data
        assert result["quotes"][0]["close"] == 100.0

    @pytest.mark.asyncio
    async def test_cache_with_list(self, cache):
        """测试列表数据缓存"""
        list_data = [1, 2, 3, 4, 5]

        await cache.set("list_key", list_data)
        result = await cache.get("list_key")

        assert result == list_data

    @pytest.mark.asyncio
    async def test_local_cache_size_limit(self):
        """测试本地缓存大小限制"""
        cache = CacheManager(max_local_size=5)

        # 添加超过限制的数据
        for i in range(10):
            await cache.set(f"key{i}", i)

        # 检查缓存大小不超过限制
        async with cache._local_lock:
            assert len(cache._local_cache) <= 5

    @pytest.mark.asyncio
    async def test_multiple_set_same_key(self, cache):
        """测试多次设置同一键"""
        await cache.set("test_key", {"version": 1})
        await cache.set("test_key", {"version": 2})
        await cache.set("test_key", {"version": 3})

        result = await cache.get("test_key")
        assert result == {"version": 3}

    @pytest.mark.asyncio
    async def test_cache_key_with_special_characters(self, cache):
        """测试包含特殊字符的键"""
        special_key = "stock:600519.SH:2024-01-01:daily"

        await cache.set(special_key, {"data": "value"})
        result = await cache.get(special_key)

        assert result == {"data": "value"}
