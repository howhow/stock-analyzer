"""
布隆过滤器

用于防止缓存穿透
"""

import math
from typing import Any

import mmh3
from redis.asyncio import Redis

from app.utils.logger import get_logger

logger = get_logger(__name__)


class BloomFilter:
    """
    布隆过滤器

    使用Redis存储位图，支持分布式环境
    """

    def __init__(
        self,
        redis_client: Redis,
        name: str = "bloom_filter",
        expected_items: int = 100000,
        false_positive_rate: float = 0.01,
    ):
        """
        初始化布隆过滤器

        Args:
            redis_client: Redis客户端
            name: 过滤器名称
            expected_items: 预期元素数量
            false_positive_rate: 误判率
        """
        self._redis = redis_client
        self._name = name
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate

        # 计算最优参数
        self._size = self._calculate_size(expected_items, false_positive_rate)
        self._hash_count = self._calculate_hash_count(self._size, expected_items)

        logger.info(
            "bloom_filter_initialized",
            name=name,
            size=self._size,
            hash_count=self._hash_count,
            expected_items=expected_items,
        )

    @staticmethod
    def _calculate_size(n: int, p: float) -> int:
        """
        计算位数组大小

        公式: m = -n * ln(p) / (ln(2)^2)

        Args:
            n: 预期元素数量
            p: 误判率

        Returns:
            位数组大小
        """
        m = -n * math.log(p) / (math.log(2) ** 2)
        return int(math.ceil(m))

    @staticmethod
    def _calculate_hash_count(m: int, n: int) -> int:
        """
        计算哈希函数数量

        公式: k = m/n * ln(2)

        Args:
            m: 位数组大小
            n: 预期元素数量

        Returns:
            哈希函数数量
        """
        k = m / n * math.log(2)
        return int(math.ceil(k))

    def _get_positions(self, item: Any) -> list[int]:
        """
        获取哈希位置

        使用双重哈希生成多个位置

        Args:
            item: 元素

        Returns:
            位置列表
        """
        item_str = str(item).encode("utf-8")

        # 使用MurmurHash3
        hash1 = mmh3.hash(item_str, 0)
        # 确保seed在有效范围内（有符号32位整数）
        seed = hash1 & 0x7FFFFFFF  # 取绝对值确保为正数
        hash2 = mmh3.hash(item_str, seed)

        positions = []
        for i in range(self._hash_count):
            # 双重哈希: h(i) = h1 + i * h2
            pos = (hash1 + i * hash2) % self._size
            positions.append(pos)

        return positions

    async def add(self, item: Any) -> None:
        """
        添加元素

        Args:
            item: 元素
        """
        positions = self._get_positions(item)

        # 批量设置位
        pipe = self._redis.pipeline()
        for pos in positions:
            pipe.setbit(self._name, pos, 1)
        await pipe.execute()

        logger.debug("bloom_filter_add", item=str(item)[:50])

    async def contains(self, item: Any) -> bool:
        """
        检查元素是否存在

        Args:
            item: 元素

        Returns:
            是否可能存在（可能有误判）
        """
        positions = self._get_positions(item)

        # 批量获取位
        pipe = self._redis.pipeline()
        for pos in positions:
            pipe.getbit(self._name, pos)
        bits = await pipe.execute()

        # 所有位都为1才返回True
        return all(bits)

    async def add_many(self, items: list[Any]) -> None:
        """
        批量添加元素

        Args:
            items: 元素列表
        """
        pipe = self._redis.pipeline()

        for item in items:
            positions = self._get_positions(item)
            for pos in positions:
                pipe.setbit(self._name, pos, 1)

        await pipe.execute()

        logger.info("bloom_filter_add_many", count=len(items))

    async def clear(self) -> None:
        """清空过滤器"""
        await self._redis.delete(self._name)
        logger.info("bloom_filter_cleared", name=self._name)

    async def count(self) -> int:
        """
        估算元素数量

        公式: n ≈ -m/k * ln(1 - X/m)

        Returns:
            估算的元素数量
        """
        # 获取设置的位数
        bits_set = await self._redis.bitcount(self._name)

        if bits_set == 0:
            return 0

        # 估算元素数量
        n = -self._size / self._hash_count * math.log(1 - bits_set / self._size)
        return int(math.ceil(n))


class LocalBloomFilter:
    """
    本地布隆过滤器

    不依赖Redis，适用于单机环境
    """

    def __init__(
        self,
        expected_items: int = 100000,
        false_positive_rate: float = 0.01,
    ):
        """
        初始化本地布隆过滤器

        Args:
            expected_items: 预期元素数量
            false_positive_rate: 误判率
        """
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate

        # 计算参数
        self._size = BloomFilter._calculate_size(expected_items, false_positive_rate)
        self._hash_count = BloomFilter._calculate_hash_count(self._size, expected_items)

        # 初始化位数组
        self._bits = [0] * self._size

        logger.info(
            "local_bloom_filter_initialized",
            size=self._size,
            hash_count=self._hash_count,
        )

    def _get_positions(self, item: Any) -> list[int]:
        """获取哈希位置"""
        item_str = str(item).encode("utf-8")

        hash1 = mmh3.hash(item_str, 0)
        # 确保seed在有效范围内
        seed = hash1 & 0x7FFFFFFF
        hash2 = mmh3.hash(item_str, seed)

        positions = []
        for i in range(self._hash_count):
            pos = (hash1 + i * hash2) % self._size
            positions.append(pos)

        return positions

    def add(self, item: Any) -> None:
        """添加元素"""
        positions = self._get_positions(item)
        for pos in positions:
            self._bits[pos] = 1

    def contains(self, item: Any) -> bool:
        """检查元素是否存在"""
        positions = self._get_positions(item)
        return all(self._bits[pos] == 1 for pos in positions)

    def clear(self) -> None:
        """清空过滤器"""
        self._bits = [0] * self._size
