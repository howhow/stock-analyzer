"""缓存管理测试"""

import pytest
from datetime import datetime

from app.core.cache import CacheManager


class TestCacheManager:
    """缓存管理器测试"""

    def test_init(self):
        """测试初始化"""
        cache = CacheManager(redis_url="", max_local_size=100)
        assert cache.max_local_size == 100
        assert cache.default_ttl == 1800

    def test_set_get_local(self):
        """测试本地缓存"""
        cache = CacheManager(redis_url="", max_local_size=100)
        
        # 设置缓存
        cache.set("test_key", {"data": "test_value"}, ttl=60)
        
        # 获取缓存
        result = cache.get("test_key")
        assert result is not None
        assert result["data"] == "test_value"

    def test_delete_local(self):
        """测试删除本地缓存"""
        cache = CacheManager(redis_url="")
        
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        cache.delete("test_key")
        assert cache.get("test_key") is None

    def test_clear_local(self):
        """测试清空本地缓存"""
        cache = CacheManager(redis_url="")
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = CacheManager(redis_url="", max_local_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # 应该淘汰key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_get_stats(self):
        """测试获取统计信息"""
        cache = CacheManager(redis_url="")
        
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key_not_exist")  # miss
        
        stats = cache.get_stats()
        assert stats["local_size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
