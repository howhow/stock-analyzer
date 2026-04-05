"""
分布式锁测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.distributed_lock import DistributedLock, DistributedLockManager


class TestDistributedLock:
    """分布式锁测试"""

    def test_init(self) -> None:
        """测试初始化"""
        lock = DistributedLock(
            redis_client=None,  # 测试用None
            key="test_lock",
            timeout=30,
        )

        assert lock._key == "lock:test_lock"
        assert lock._timeout == 30
        assert lock._token is not None
        assert lock._locked is False

    def test_key_prefix(self) -> None:
        """测试键前缀"""
        lock = DistributedLock(
            redis_client=None,
            key="my_resource",
        )

        assert lock._key == "lock:my_resource"

    def test_token_uniqueness(self) -> None:
        """测试令牌唯一性"""
        lock1 = DistributedLock(redis_client=None, key="lock1")
        lock2 = DistributedLock(redis_client=None, key="lock2")

        assert lock1._token != lock2._token


class TestDistributedLockManager:
    """分布式锁管理器测试"""

    def test_init(self) -> None:
        """测试初始化"""
        manager = DistributedLockManager()

        assert manager._redis_url is not None
        assert manager._redis is None

    def test_init_with_url(self) -> None:
        """测试使用URL初始化"""
        url = "redis://localhost:6379/1"
        manager = DistributedLockManager(redis_url=url)

        assert manager._redis_url == url


class TestDistributedLockContext:
    """分布式锁上下文管理器测试"""

    @pytest.mark.asyncio
    async def test_context_manager_without_redis(self) -> None:
        """测试无Redis时的上下文管理器"""
        # 模拟Redis不可用的情况
        lock = DistributedLock(
            redis_client=None,
            key="test_lock",
            retry_times=1,
        )

        # 无Redis时acquire会失败
        acquired = await lock.acquire()
        assert acquired is False

    @pytest.mark.asyncio
    async def test_release_without_acquire(self) -> None:
        """测试未获取就释放"""
        lock = DistributedLock(redis_client=None, key="test_lock")

        # 未获取锁就释放
        result = await lock.release()
        assert result is False


class TestLockParameters:
    """锁参数测试"""

    def test_default_parameters(self) -> None:
        """测试默认参数"""
        lock = DistributedLock(redis_client=None, key="test")

        assert lock._timeout == 30
        assert lock._retry_times == 3
        assert lock._retry_delay == 0.1

    def test_custom_parameters(self) -> None:
        """测试自定义参数"""
        lock = DistributedLock(
            redis_client=None,
            key="test",
            timeout=60,
            retry_times=5,
            retry_delay=0.5,
        )

        assert lock._timeout == 60
        assert lock._retry_times == 5
        assert lock._retry_delay == 0.5


class TestDistributedLockWithRedis:
    """有Redis的分布式锁测试"""

    @pytest.mark.asyncio
    async def test_acquire_with_mock_redis(self) -> None:
        """测试使用mock Redis获取锁"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)

        lock = DistributedLock(
            redis_client=mock_redis,
            key="test_lock",
            retry_times=1,
        )

        acquired = await lock.acquire()
        assert acquired is True
        assert lock._locked is True

    @pytest.mark.asyncio
    async def test_release_with_mock_redis(self) -> None:
        """测试使用mock Redis释放锁"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(return_value=1)

        lock = DistributedLock(
            redis_client=mock_redis,
            key="test_lock",
            retry_times=1,
        )

        # 先获取锁
        await lock.acquire()
        # 然后释放
        result = await lock.release()
        assert result is True

    @pytest.mark.asyncio
    async def test_extend_with_mock_redis(self) -> None:
        """测试延长锁时间"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(return_value=1)

        lock = DistributedLock(
            redis_client=mock_redis,
            key="test_lock",
            retry_times=1,
        )

        # 先获取锁
        await lock.acquire()
        # 延长时间
        result = await lock.extend(60)
        assert result is True
