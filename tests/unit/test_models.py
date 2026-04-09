"""
数据库模型测试

测试UserConfig和AnalysisHistory模型
"""

from datetime import datetime

import pytest

from app.models.analysis_history import AnalysisHistory
from app.models.user_config import UserConfig


class TestUserConfig:
    """测试UserConfig模型"""

    def test_create_user_config(self):
        """测试创建用户配置"""
        config = UserConfig(
            user_id="test_user",
            openai_api_key="encrypted_key",
            openai_base_url="https://api.openai.com/v1",
            openai_model="gpt-4-turbo",
            default_analysis_type="both",
            default_days=120,
        )

        assert config.user_id == "test_user"
        assert config.openai_api_key == "encrypted_key"
        assert config.default_analysis_type == "both"
        assert config.default_days == 120

    def test_user_config_defaults(self):
        """测试用户配置默认值"""
        config = UserConfig(
            user_id="test_user",
            default_analysis_type="both",  # 必须提供
            default_days=120,  # 必须提供
        )

        assert config.default_analysis_type == "both"
        assert config.default_days == 120
        assert config.feishu_push_enabled is False

    def test_user_config_repr(self):
        """测试用户配置字符串表示"""
        config = UserConfig(user_id="test_user", id=1)
        repr_str = repr(config)

        assert "UserConfig" in repr_str
        assert "id=1" in repr_str
        assert "user_id=test_user" in repr_str


class TestAnalysisHistory:
    """测试AnalysisHistory模型"""

    def test_create_analysis_history(self):
        """测试创建分析历史"""
        history = AnalysisHistory(
            user_id="test_user",
            stock_code="600276.SH",
            stock_name="恒瑞医药",
            analysis_type="both",
            total_score=4.5,
            fundamental_score=4.0,
            technical_score=5.0,
            recommendation="买入",
            analysis_result='{"details": "test"}',
            analysis_duration_ms=1500,
        )

        assert history.user_id == "test_user"
        assert history.stock_code == "600276.SH"
        assert history.total_score == 4.5
        assert history.recommendation == "买入"

    def test_analysis_history_repr(self):
        """测试分析历史字符串表示"""
        history = AnalysisHistory(
            id=1,
            user_id="test_user",
            stock_code="600276.SH",
            stock_name="恒瑞医药",
            analysis_type="both",
            total_score=4.5,
            recommendation="买入",
            analysis_result="{}",
            analysis_duration_ms=1500,
        )
        repr_str = repr(history)

        assert "AnalysisHistory" in repr_str
        assert "id=1" in repr_str
        assert "stock_code=600276.SH" in repr_str

    def test_analysis_history_optional_fields(self):
        """测试分析历史可选字段"""
        history = AnalysisHistory(
            user_id="test_user",
            stock_code="600276.SH",
            analysis_type="technical",
            total_score=3.5,
            recommendation="持有",
            analysis_result="{}",
            analysis_duration_ms=1000,
        )

        assert history.stock_name is None
        assert history.fundamental_score is None
        assert history.technical_score is None
