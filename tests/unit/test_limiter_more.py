"""
Limiter补充测试 - 提升覆盖率
"""

import pytest
from unittest.mock import AsyncMock

from app.core.limiter import (
    SlidingWindowLimiter,
    RateLimiter,
    UserTier,
    get_rate_limiter,
)


class TestSlidingWindowLimiterMore:
    """滑动窗口限流器补充测试"""

    @pytest.mark.asyncio
    async def test_is_allowed_with_mock_redis(self):
        """测试使用mock Redis检查限流"""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 9, 60])

        limiter = SlidingWindowLimiter(redis_client=mock_redis)
        allowed, remaining, reset_time = await limiter.is_allowed("test_key", 10, 60)

        assert allowed is True
        assert remaining == 9
        assert reset_time == 60

    @pytest.mark.asyncio
    async def test_is_denied_with_mock_redis(self):
        """测试被限流拒绝"""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[0, 0, 30])

        limiter = SlidingWindowLimiter(redis_client=mock_redis)
        allowed, remaining, reset_time = await limiter.is_allowed("test_key", 10, 60)

        assert allowed is False
        assert remaining == 0
        assert reset_time == 30

    @pytest.mark.asyncio
    async def test_redis_error_fallback(self):
        """测试Redis错误降级"""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=Exception("Redis error"))

        limiter = SlidingWindowLimiter(redis_client=mock_redis)
        # Redis错误时应该降级允许请求
        allowed, remaining, reset_time = await limiter.is_allowed("test_key", 10, 60)

        assert allowed is True


class TestRateLimiterMore:
    """限流管理器补充测试"""

    def test_get_rate_limiter_singleton(self):
        """测试获取全局限流器"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        # 应该返回同一个实例
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_check_limit_service_tier(self):
        """测试服务账号限流"""
        limiter = RateLimiter()

        import uuid

        user_id = f"service_{uuid.uuid4()}"

        allowed, remaining, _ = await limiter.check_limit(
            user_id, UserTier.SERVICE, "analyze"
        )

        assert allowed is True
        # 服务账号有更高的限流

    @pytest.mark.asyncio
    async def test_check_limit_ai_enhanced(self):
        """测试AI增强分析限流"""
        limiter = RateLimiter()

        import uuid

        user_id = f"user_{uuid.uuid4()}"

        allowed, remaining, _ = await limiter.check_limit(
            user_id, UserTier.FREE, "ai_enhanced"
        )

        # 免费用户每天只有5次AI增强
        assert allowed is True
