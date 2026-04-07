"""
限流器模块完整测试

目标覆盖率: ≥ 95%
当前覆盖率: 73%
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request

from app.core.limiter import (
    RATE_LIMITS,
    RateLimiter,
    SlidingWindowLimiter,
    UserTier,
    check_rate_limit,
    get_rate_limiter,
    rate_limit,
    rate_limit_middleware,
)


class TestSlidingWindowLimiterLocal:
    """滑动窗口限流器本地缓存测试"""

    @pytest.fixture
    def limiter(self):
        """创建限流器（无Redis）"""
        return SlidingWindowLimiter(redis_client=None)

    @pytest.mark.asyncio
    async def test_is_allowed_local_within_limit(self, limiter):
        """测试本地限流 - 在限制内"""
        allowed, remaining, reset_time = await limiter.is_allowed(
            "test_key", max_requests=10, window_seconds=60
        )

        assert allowed is True
        assert remaining == 9
        assert reset_time == 60

    @pytest.mark.asyncio
    async def test_is_allowed_local_exceed_limit(self, limiter):
        """测试本地限流 - 超过限制"""
        # 发送 10 个请求
        for _ in range(10):
            await limiter.is_allowed("test_key", max_requests=10, window_seconds=60)

        # 第 11 个请求应该被拒绝
        allowed, remaining, reset_time = await limiter.is_allowed(
            "test_key", max_requests=10, window_seconds=60
        )

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_is_allowed_local_different_keys(self, limiter):
        """测试本地限流 - 不同键隔离"""
        # 消费 key1 的所有配额
        for _ in range(10):
            await limiter.is_allowed("key1", max_requests=10, window_seconds=60)

        # key2 应该仍然可用
        allowed, remaining, _ = await limiter.is_allowed(
            "key2", max_requests=10, window_seconds=60
        )

        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_is_allowed_local_window_expired(self, limiter):
        """测试本地限流 - 窗口过期"""
        # 发送 10 个请求
        for _ in range(10):
            await limiter.is_allowed("test_key", max_requests=10, window_seconds=1)

        # 等待窗口过期
        await asyncio.sleep(1.1)

        # 应该允许新请求
        allowed, remaining, _ = await limiter.is_allowed(
            "test_key", max_requests=10, window_seconds=1
        )

        assert allowed is True


class TestRateLimiter:
    """限流器管理器测试"""

    @pytest.fixture
    def rate_limiter(self):
        """创建限流器管理器"""
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_check_limit_free_tier(self, rate_limiter):
        """测试免费用户限流"""
        # 免费用户：analyze 10次/分钟
        for _ in range(10):
            allowed, _, _ = await rate_limiter.check_limit(
                "user1", UserTier.FREE, "analyze"
            )
            assert allowed is True

        # 第 11 次应该被拒绝
        allowed, remaining, _ = await rate_limiter.check_limit(
            "user1", UserTier.FREE, "analyze"
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_limit_pro_tier(self, rate_limiter):
        """测试专业用户限流"""
        # 专业用户：analyze 60次/分钟
        for _ in range(60):
            allowed, _, _ = await rate_limiter.check_limit(
                "user1", UserTier.PRO, "analyze"
            )
            assert allowed is True

        # 第 61 次应该被拒绝
        allowed, _, _ = await rate_limiter.check_limit("user1", UserTier.PRO, "analyze")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_limit_enterprise_tier(self, rate_limiter):
        """测试企业用户限流"""
        # 企业用户：analyze 300次/分钟
        for _ in range(300):
            allowed, _, _ = await rate_limiter.check_limit(
                "user1", UserTier.ENTERPRISE, "analyze"
            )
            assert allowed is True

        # 第 301 次应该被拒绝
        allowed, _, _ = await rate_limiter.check_limit(
            "user1", UserTier.ENTERPRISE, "analyze"
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_get_tier_from_role(self, rate_limiter):
        """测试从角色获取用户等级"""
        assert rate_limiter.get_tier_from_role("free") == UserTier.FREE
        assert rate_limiter.get_tier_from_role("pro") == UserTier.PRO
        assert rate_limiter.get_tier_from_role("enterprise") == UserTier.ENTERPRISE
        assert rate_limiter.get_tier_from_role("service") == UserTier.SERVICE
        assert rate_limiter.get_tier_from_role("unknown") == UserTier.FREE


class TestCheckRateLimit:
    """check_rate_limit 函数测试"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_anonymous_user(self):
        """测试匿名用户限流"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = None

        result = await check_rate_limit(request, "analyze")

        assert result["allowed"] is True
        assert result["tier"] == "free"

    @pytest.mark.asyncio
    async def test_check_rate_limit_authenticated_user(self):
        """测试认证用户限流"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = {"user_id": "user123", "role": "pro"}

        result = await check_rate_limit(request, "analyze")

        assert result["allowed"] is True
        assert result["tier"] == "pro"

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """测试限流超出"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = None

        # 消费所有配额
        for _ in range(10):
            await check_rate_limit(request, "analyze")

        # 第 11 次应该抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(request, "analyze")

        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers


class TestRateLimitDecorator:
    """限流装饰器测试"""

    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """测试限流装饰器"""
        decorator = rate_limit("analyze")

        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = None

        result = await decorator(request)

        assert result["allowed"] is True
        assert "remaining" in result


class TestRateLimitMiddleware:
    """限流中间件测试"""

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_with_headers(self):
        """测试限流中间件 - 添加响应头"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.rate_limit_remaining = 5
        request.state.rate_limit_reset = 60

        response = Mock()
        response.headers = {}

        async def call_next(req):
            return response

        result = await rate_limit_middleware(request, call_next)

        assert "X-RateLimit-Remaining" in result.headers
        assert result.headers["X-RateLimit-Remaining"] == "5"
        assert "X-RateLimit-Reset" in result.headers
        assert result.headers["X-RateLimit-Reset"] == "60"

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_without_headers(self):
        """测试限流中间件 - 无限流信息"""
        request = Mock(spec=Request)
        request.state = Mock()
        # 没有限流信息

        response = Mock()
        response.headers = {}

        async def call_next(req):
            return response

        result = await rate_limit_middleware(request, call_next)

        # 应该不添加限流响应头
        assert "X-RateLimit-Remaining" not in result.headers


class TestGetRateLimiter:
    """get_rate_limiter 函数测试"""

    def test_get_rate_limiter_singleton(self):
        """测试限流器单例"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2


class TestUserTierConfig:
    """用户等级配置测试"""

    def test_rate_limits_config(self):
        """测试限流配置"""
        # 免费用户配置
        assert RATE_LIMITS[UserTier.FREE]["analyze"] == (10, 60)
        assert RATE_LIMITS[UserTier.FREE]["batch_analyze"] == (2, 60)
        assert RATE_LIMITS[UserTier.FREE]["ai_enhanced"] == (5, 86400)

        # 专业用户配置
        assert RATE_LIMITS[UserTier.PRO]["analyze"] == (60, 60)
        assert RATE_LIMITS[UserTier.PRO]["batch_analyze"] == (10, 60)

        # 企业用户配置
        assert RATE_LIMITS[UserTier.ENTERPRISE]["analyze"] == (300, 60)
        assert RATE_LIMITS[UserTier.ENTERPRISE]["batch_analyze"] == (30, 60)

        # 服务账号配置
        assert RATE_LIMITS[UserTier.SERVICE]["analyze"] == (1000, 60)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.core.limiter", "--cov-report=term-missing"])
