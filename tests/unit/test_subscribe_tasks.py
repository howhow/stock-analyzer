"""
订阅任务测试

测试用户订阅相关的 Celery 任务。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.tasks.subscribe_tasks import (
    _cancel_subscription_logic,
    _create_subscription_logic,
    _execute_subscriptions_logic,
    _send_notification_logic,
)


# ============================================================
# _execute_subscriptions_logic
# ============================================================


class TestExecuteSubscriptionsLogic:
    """测试执行订阅核心逻辑"""

    @patch("app.tasks.subscribe_tasks.async_analyze_and_report")
    def test_execute_empty_subscriptions(self, mock_async):
        """测试空订阅列表"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _execute_subscriptions_logic(mock_self)

        assert result["status"] == "success"
        assert result["total"] == 0
        assert result["executed"] == 0
        assert result["failed"] == 0

    @patch("app.tasks.subscribe_tasks.async_analyze_and_report")
    def test_execute_with_subscriptions(self, mock_async):
        """测试有订阅的情况"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _execute_subscriptions_logic(mock_self)

        assert result["status"] == "success"


# ============================================================
# _create_subscription_logic
# ============================================================


class TestCreateSubscriptionLogic:
    """测试创建订阅核心逻辑"""

    def test_create_success(self):
        """测试正常创建"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _create_subscription_logic(
            mock_self,
            user_id="user_001",
            stock_code="600519.SH",
        )

        assert result["status"] == "success"
        assert result["user_id"] == "user_001"
        assert result["stock_code"] == "600519.SH"
        assert "subscription_id" in result

    def test_create_with_custom_params(self):
        """测试自定义参数"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _create_subscription_logic(
            mock_self,
            user_id="user_001",
            stock_code="600519.SH",
            analysis_type="technical",
            schedule="weekly",
        )

        assert result["status"] == "success"


# ============================================================
# _cancel_subscription_logic
# ============================================================


class TestCancelSubscriptionLogic:
    """测试取消订阅核心逻辑"""

    def test_cancel_success(self):
        """测试正常取消"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _cancel_subscription_logic(
            mock_self,
            subscription_id="sub_001",
        )

        assert result["status"] == "success"
        assert result["subscription_id"] == "sub_001"


# ============================================================
# _send_notification_logic
# ============================================================


class TestSendNotificationLogic:
    """测试发送通知核心逻辑"""

    def test_send_success(self):
        """测试正常发送"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _send_notification_logic(
            mock_self,
            user_id="user_001",
            title="测试通知",
            content="这是测试内容",
        )

        assert result["status"] == "success"
        assert result["user_id"] == "user_001"
        assert result["channel"] == "feishu"

    def test_send_with_email_channel(self):
        """测试邮件渠道"""
        mock_self = MagicMock()
        mock_self.request.id = "task_001"

        result = _send_notification_logic(
            mock_self,
            user_id="user_001",
            title="测试通知",
            content="这是测试内容",
            channel="email",
        )

        assert result["status"] == "success"
        assert result["channel"] == "email"
