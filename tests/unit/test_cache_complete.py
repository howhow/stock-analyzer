"""
缓存管理器完整测试

目标覆盖率: ≥ 90%
当前覆盖率: 85%
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.cache import CacheManager


class TestCacheManagerRedisConnection:
    """Redis 连接测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="redis://localhost:6379/0")

    @pytest.mark.asyncio
    async def test_get_redis_connection_success(self, cache_manager):
        """测试 Redis 连接成功"""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis

            result = await cache_manager._get_redis()

            assert result is mock_redis
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_connection_failure(self, cache_manager):
        """测试 Redis 连接失败"""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection refused")

            result = await cache_manager._get_redis()

            assert result is None


class TestCacheManagerGet:
    """缓存获取测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="", max_local_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_get_from_local_cache(self, cache_manager):
        """测试从本地缓存获取"""
        # 设置本地缓存
        await cache_manager._set_local("test_key", "test_value", ttl=60)

        result = await cache_manager.get("test_key")

        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_from_redis_cache(self, cache_manager):
        """测试从 Redis 缓存获取"""
        with patch.object(cache_manager, "_get_redis_cache") as mock_get_redis:
            mock_get_redis.return_value = "redis_value"

            result = await cache_manager.get("test_key")

            assert result == "redis_value"

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache_manager):
        """测试缓存未命中"""
        result = await cache_manager.get("nonexistent_key")

        assert result is None


class TestCacheManagerSet:
    """缓存设置测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="", max_local_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_with_default_ttl(self, cache_manager):
        """测试使用默认 TTL 设置缓存"""
        result = await cache_manager.set("test_key", "test_value")

        assert result is True

        # 验证本地缓存
        local_value = await cache_manager._get_local("test_key")
        assert local_value == "test_value"

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager):
        """测试使用自定义 TTL 设置缓存"""
        result = await cache_manager.set("test_key", "test_value", ttl=120)

        assert result is True


class TestCacheManagerDelete:
    """缓存删除测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="", max_local_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_delete_local_cache(self, cache_manager):
        """测试删除本地缓存"""
        # 设置缓存
        await cache_manager._set_local("test_key", "test_value", ttl=60)

        # 删除缓存
        result = await cache_manager.delete("test_key")

        assert result is True

        # 验证已删除
        local_value = await cache_manager._get_local("test_key")
        assert local_value is None

    @pytest.mark.asyncio
    async def test_delete_redis_cache(self, cache_manager):
        """测试删除 Redis 缓存"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            result = await cache_manager.delete("test_key")

            assert result is True
            mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_redis_failure(self, cache_manager):
        """测试删除 Redis 缓存失败"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Delete failed"))

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            # 应该不抛出异常
            result = await cache_manager.delete("test_key")

            assert result is True


class TestCacheManagerLocalCache:
    """本地缓存测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="", max_local_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get_local(self, cache_manager):
        """测试本地缓存设置和获取"""
        await cache_manager._set_local("test_key", "test_value", ttl=60)

        result = await cache_manager._get_local("test_key")

        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_expired_local_cache(self, cache_manager):
        """测试获取过期的本地缓存"""
        # 设置已过期的缓存
        await cache_manager._set_local("test_key", "test_value", ttl=0)

        # 等待过期
        await asyncio.sleep(0.1)

        result = await cache_manager._get_local("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_expired_entries(self, cache_manager):
        """测试清理过期缓存条目"""
        # 设置缓存
        await cache_manager._set_local("key1", "value1", ttl=0)
        await cache_manager._set_local("key2", "value2", ttl=60)

        # 等待过期
        await asyncio.sleep(0.1)

        # 清理过期条目
        await cache_manager._clear_expired()

        # 验证 key1 已被清理
        result = await cache_manager._get_local("key1")
        assert result is None

        # 验证 key2 仍然存在
        result = await cache_manager._get_local("key2")
        assert result == "value2"


class TestCacheManagerRedisCache:
    """Redis 缓存测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        return CacheManager(redis_url="", max_local_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_redis_cache(self, cache_manager):
        """测试设置 Redis 缓存"""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            await cache_manager._set_redis_cache("test_key", "test_value", ttl=60)

            # 验证调用了 setex
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_redis_cache_failure(self, cache_manager):
        """测试设置 Redis 缓存失败"""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Set failed"))

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            # 应该不抛出异常
            await cache_manager._set_redis_cache("test_key", "test_value", ttl=60)

    @pytest.mark.asyncio
    async def test_get_redis_cache_success(self, cache_manager):
        """测试获取 Redis 缓存成功"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"value": "test_value"}')

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            result = await cache_manager._get_redis_cache("test_key")

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_redis_cache_not_found(self, cache_manager):
        """测试获取 Redis 缓存未找到"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch.object(cache_manager, "_get_redis") as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            result = await cache_manager._get_redis_cache("test_key")

            assert result is None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.core.cache", "--cov-report=term-missing"])
