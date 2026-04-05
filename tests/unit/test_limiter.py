"""
限流器测试
"""

import pytest

from app.core.limiter import (
    RATE_LIMITS,
    UserTier,
    RateLimiter,
    SlidingWindowLimiter,
)


class TestUserTier:
    """用户等级测试"""

    def test_user_tier_values(self) -> None:
        """测试用户等级值"""
        assert UserTier.FREE.value == "free"
        assert UserTier.PRO.value == "pro"
        assert UserTier.ENTERPRISE.value == "enterprise"
        assert UserTier.SERVICE.value == "service"


class TestRateLimits:
    """限流配置测试"""

    def test_free_tier_limits(self) -> None:
        """测试免费等级限流"""
        limits = RATE_LIMITS[UserTier.FREE]

        assert limits["analyze"] == (10, 60)
        assert limits["batch_analyze"] == (2, 60)
        assert limits["ai_enhanced"] == (5, 86400)

    def test_pro_tier_limits(self) -> None:
        """测试Pro等级限流"""
        limits = RATE_LIMITS[UserTier.PRO]

        assert limits["analyze"] == (60, 60)
        assert limits["batch_analyze"] == (10, 60)

    def test_enterprise_tier_limits(self) -> None:
        """测试企业等级限流"""
        limits = RATE_LIMITS[UserTier.ENTERPRISE]

        assert limits["analyze"] == (300, 60)

    def test_service_tier_limits(self) -> None:
        """测试服务账号限流"""
        limits = RATE_LIMITS[UserTier.SERVICE]

        assert limits["analyze"] == (1000, 60)


class TestSlidingWindowLimiter:
    """滑动窗口限流器测试"""

    def test_init(self) -> None:
        """测试初始化"""
        limiter = SlidingWindowLimiter()
        assert limiter._redis is None
        assert limiter._local_cache == {}

    def test_check_with_local_allowed(self) -> None:
        """测试本地限流允许"""
        limiter = SlidingWindowLimiter()
        key = "test_key_1"

        allowed, remaining, reset_time = limiter._check_with_local(key, 10, 60)

        assert allowed is True
        assert remaining == 9
        assert reset_time == 60

    def test_check_with_local_exceeded(self) -> None:
        """测试本地限流超限"""
        limiter = SlidingWindowLimiter()
        key = "test_key_2"

        # 连续请求直到超限（限制10次）
        for i in range(11):
            allowed, remaining, _ = limiter._check_with_local(key, 10, 60)
            if i < 10:
                assert allowed is True, f"Request {i+1} should be allowed"
            else:
                # 第11次应该被拒绝
                assert allowed is False, f"Request {i+1} should be denied"
                assert remaining == 0

    def test_check_with_local_different_keys(self) -> None:
        """测试不同键独立限流"""
        limiter = SlidingWindowLimiter()

        # 对key1请求5次
        for _ in range(5):
            limiter._check_with_local("key1", 10, 60)

        # key2仍然有10次
        allowed, remaining, _ = limiter._check_with_local("key2", 10, 60)
        assert allowed is True
        assert remaining == 9


class TestRateLimiter:
    """限流管理器测试"""

    def test_init(self) -> None:
        """测试初始化"""
        limiter = RateLimiter()
        assert limiter._limiter is not None

    def test_get_tier_from_role(self) -> None:
        """测试从角色获取等级"""
        limiter = RateLimiter()

        assert limiter.get_tier_from_role("admin") == UserTier.ENTERPRISE
        assert limiter.get_tier_from_role("pro") == UserTier.PRO
        assert limiter.get_tier_from_role("user") == UserTier.FREE
        assert limiter.get_tier_from_role("guest") == UserTier.FREE
        assert limiter.get_tier_from_role("service") == UserTier.SERVICE
        assert limiter.get_tier_from_role("unknown") == UserTier.FREE

    @pytest.mark.asyncio
    async def test_check_limit_free_tier(self) -> None:
        """测试免费等级限流检查"""
        limiter = RateLimiter()

        # 使用唯一的用户ID避免缓存冲突
        import uuid

        user_id = f"user_{uuid.uuid4()}"

        allowed, remaining, reset_time = await limiter.check_limit(
            user_id, UserTier.FREE, "analyze"
        )

        assert allowed is True
        # 由于Redis不可用，降级返回max_requests
        # 使用本地缓存时应返回正确的remaining
        assert remaining >= 0  # 确保remaining非负

    @pytest.mark.asyncio
    async def test_check_limit_different_tiers(self) -> None:
        """测试不同等级限流"""
        limiter = RateLimiter()

        # 免费用户
        _, free_remaining, _ = await limiter.check_limit(
            "user_free", UserTier.FREE, "analyze"
        )

        # Pro用户
        _, pro_remaining, _ = await limiter.check_limit(
            "user_pro", UserTier.PRO, "analyze"
        )

        # Pro用户剩余次数更多
        assert pro_remaining > free_remaining
