"""
BloomFilter补充测试 - 提升覆盖率
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.bloom_filter import BloomFilter, LocalBloomFilter


class TestBloomFilterWithRedis:
    """BloomFilter Redis版本测试"""

    @pytest.mark.asyncio
    async def test_bloom_filter_with_mock_redis(self):
        """测试使用mock Redis的布隆过滤器"""
        mock_redis = AsyncMock()
        mock_redis.setbit = AsyncMock(return_value=1)
        mock_redis.getbit = AsyncMock(return_value=1)
        mock_redis.pipeline = MagicMock()
        mock_pipe = AsyncMock()
        mock_pipe.setbit = AsyncMock()
        mock_pipe.getbit = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[1, 1, 1, 1, 1])
        mock_redis.pipeline.return_value = mock_pipe

        bf = BloomFilter(
            redis_client=mock_redis,
            name="test_filter",
            expected_items=1000,
        )

        # 测试添加
        await bf.add("test_item")

        # 测试检查
        result = await bf.contains("test_item")
        # 由于mock返回全1，应该返回True
        assert result is True

    @pytest.mark.asyncio
    async def test_bloom_filter_add_many(self):
        """测试批量添加"""
        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock()
        mock_pipe = AsyncMock()
        mock_pipe.setbit = AsyncMock()
        mock_pipe.execute = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipe

        bf = BloomFilter(
            redis_client=mock_redis,
            name="test_filter",
        )

        items = ["item1", "item2", "item3"]
        await bf.add_many(items)

        # 应该调用了pipeline
        assert mock_pipe.execute.called

    @pytest.mark.asyncio
    async def test_bloom_filter_clear(self):
        """测试清空过滤器"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        bf = BloomFilter(
            redis_client=mock_redis,
            name="test_filter",
        )

        await bf.clear()

        # 应该调用了delete
        assert mock_redis.delete.called

    @pytest.mark.asyncio
    async def test_bloom_filter_count(self):
        """测试估算元素数量"""
        mock_redis = AsyncMock()
        mock_redis.bitcount = AsyncMock(return_value=100)
        mock_redis.delete = AsyncMock(return_value=1)

        bf = BloomFilter(
            redis_client=mock_redis,
            name="test_filter",
        )

        result = await bf.count()

        # 应该返回一个估算数量
        assert result >= 0
