"""
API Config 完整测试

关键技巧: dependency_overrides + 替换模块级函数
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db


class TestMaskFunctions:
    """测试脱敏函数"""

    def test_mask_api_key_short(self) -> None:
        """测试短 API Key"""
        from app.api.v1.config import _mask_api_key

        assert _mask_api_key("abc") == "****"

    def test_mask_api_key_long(self) -> None:
        """测试长 API Key"""
        from app.api.v1.config import _mask_api_key

        assert _mask_api_key("sk-test-api-key-12345") == "sk-t****2345"

    def test_mask_api_key_exact_8(self) -> None:
        """测试恰好 8 字符"""
        from app.api.v1.config import _mask_api_key

        assert _mask_api_key("12345678") == "****"

    def test_mask_encrypted_key_none(self) -> None:
        """测试空加密 Key"""
        from app.api.v1.config import _mask_encrypted_key

        assert _mask_encrypted_key(None) is None

    def test_mask_encrypted_key_short(self) -> None:
        """测试短加密 Key"""
        from app.api.v1.config import _mask_encrypted_key

        assert _mask_encrypted_key("abc") == "****"

    def test_mask_encrypted_key_long(self) -> None:
        """测试长加密 Key"""
        from app.api.v1.config import _mask_encrypted_key

        result = _mask_encrypted_key("v2:abc123xyz:encrypted_data_here")
        assert result is not None
        assert "****" in result


class TestConfigAPI:
    """测试配置 API - 使用依赖覆盖"""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Mock 数据库会话"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_encryption(self) -> MagicMock:
        """Mock 加密管理器"""
        manager = MagicMock()
        manager.encrypt = MagicMock(return_value="encrypted_key")
        manager.decrypt = MagicMock(return_value="decrypted_key")
        return manager

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """创建测试客户端（覆盖依赖）"""
        app.dependency_overrides[get_db] = lambda: mock_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_create_config_success(
        self, client: TestClient, mock_db: AsyncMock, mock_encryption: MagicMock
    ) -> None:
        """测试创建配置成功"""
        # Mock 数据库查询返回 None（用户不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock refresh 设置属性
        def refresh_side_effect(obj: MagicMock) -> None:
            obj.id = 1
            obj.user_id = "test_user"
            obj.openai_api_key = "encrypted_key"
            obj.openai_base_url = None
            obj.openai_model = "gpt-4"
            obj.anthropic_api_key = None
            obj.anthropic_model = None
            obj.default_analysis_type = "both"
            obj.default_days = 120
            obj.feishu_webhook_url = None
            obj.feishu_push_enabled = False

        mock_db.refresh = AsyncMock(side_effect=refresh_side_effect)

        # 替换模块级函数
        import app.api.v1.config as config_module

        original_get_encryption = config_module.get_encryption_manager
        config_module.get_encryption_manager = MagicMock(return_value=mock_encryption)

        try:
            response = client.post(
                "/api/v1/config/",
                json={
                    "user_id": "test_user",
                    "openai_api_key": "sk-test",
                    "openai_model": "gpt-4",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "test_user"
        finally:
            config_module.get_encryption_manager = original_get_encryption

    def test_create_config_already_exists(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """测试配置已存在"""
        # Mock 数据库查询返回已存在的配置
        mock_existing = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing)
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/config/",
            json={
                "user_id": "existing_user",
                "openai_model": "gpt-4",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_config_success(
        self, client: TestClient, mock_db: AsyncMock, mock_encryption: MagicMock
    ) -> None:
        """测试获取配置成功"""
        # Mock 数据库返回配置
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.user_id = "test_user"
        mock_config.openai_api_key = "encrypted_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-4"
        mock_config.anthropic_api_key = None
        mock_config.anthropic_model = None
        mock_config.default_analysis_type = "both"
        mock_config.default_days = 120
        mock_config.feishu_webhook_url = None
        mock_config.feishu_push_enabled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_config)
        mock_db.execute = AsyncMock(return_value=mock_result)

        import app.api.v1.config as config_module

        config_module.get_encryption_manager = MagicMock(return_value=mock_encryption)

        response = client.get("/api/v1/config/test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"

    def test_get_config_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """测试配置不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/config/unknown_user")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_config_success(
        self, client: TestClient, mock_db: AsyncMock, mock_encryption: MagicMock
    ) -> None:
        """测试更新配置成功"""
        # Mock 数据库返回现有配置
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.user_id = "test_user"
        mock_config.openai_api_key = "old_encrypted_key"
        mock_config.openai_base_url = None
        mock_config.openai_model = "gpt-3.5"
        mock_config.anthropic_api_key = None
        mock_config.anthropic_model = None
        mock_config.default_analysis_type = "both"
        mock_config.default_days = 120
        mock_config.feishu_webhook_url = None
        mock_config.feishu_push_enabled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_config)
        mock_db.execute = AsyncMock(return_value=mock_result)

        import app.api.v1.config as config_module

        config_module.get_encryption_manager = MagicMock(return_value=mock_encryption)

        response = client.put(
            "/api/v1/config/test_user",
            json={
                "openai_api_key": "sk-new-key",
                "openai_model": "gpt-4-turbo",
                "default_days": 60,
            },
        )

        assert response.status_code == 200

    def test_update_config_not_found(
        self, client: TestClient, mock_db: AsyncMock, mock_encryption: MagicMock
    ) -> None:
        """测试更新配置不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        import app.api.v1.config as config_module

        config_module.get_encryption_manager = MagicMock(return_value=mock_encryption)

        response = client.put(
            "/api/v1/config/nonexistent",
            json={"openai_model": "gpt-4"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_config_all_fields(
        self, client: TestClient, mock_db: AsyncMock, mock_encryption: MagicMock
    ) -> None:
        """测试更新所有字段"""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.user_id = "test_user"
        mock_config.openai_api_key = None
        mock_config.openai_base_url = None
        mock_config.openai_model = None
        mock_config.anthropic_api_key = None
        mock_config.anthropic_model = None
        mock_config.default_analysis_type = "both"
        mock_config.default_days = 120
        mock_config.feishu_webhook_url = None
        mock_config.feishu_push_enabled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_config)
        mock_db.execute = AsyncMock(return_value=mock_result)

        import app.api.v1.config as config_module

        config_module.get_encryption_manager = MagicMock(return_value=mock_encryption)

        response = client.put(
            "/api/v1/config/test_user",
            json={
                "openai_api_key": "new-key",
                "openai_base_url": "https://new.api.com/v1",
                "openai_model": "gpt-4",
                "anthropic_api_key": "new-anthropic",
                "anthropic_model": "claude-3-opus",
                "default_analysis_type": "technical",
                "default_days": 30,
                "feishu_webhook_url": "https://webhook.feishu.cn/test",
                "feishu_push_enabled": True,
            },
        )

        assert response.status_code == 200
