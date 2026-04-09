"""
用户配置API

提供用户配置的CRUD操作
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user_config import UserConfig
from app.utils.encryption import get_encryption_manager

router = APIRouter(prefix="/config", tags=["config"])


class UserConfigCreate(BaseModel):
    """用户配置创建请求"""

    user_id: str = Field(..., description="用户ID")
    openai_api_key: str | None = Field(None, description="OpenAI API Key")
    openai_base_url: str | None = Field(None, description="OpenAI Base URL")
    openai_model: str | None = Field(None, description="OpenAI Model")
    anthropic_api_key: str | None = Field(None, description="Anthropic API Key")
    anthropic_model: str | None = Field(None, description="Anthropic Model")
    default_analysis_type: str = Field("both", description="默认分析类型")
    default_days: int = Field(120, description="默认分析天数")


class UserConfigResponse(BaseModel):
    """用户配置响应"""

    id: int
    user_id: str
    openai_api_key: str | None = Field(None, description="OpenAI API Key（脱敏）")
    openai_base_url: str | None
    openai_model: str | None
    anthropic_api_key: str | None = Field(None, description="Anthropic API Key（脱敏）")
    anthropic_model: str | None
    default_analysis_type: str
    default_days: int
    feishu_webhook_url: str | None
    feishu_push_enabled: bool


class UserConfigUpdate(BaseModel):
    """用户配置更新请求"""

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    default_analysis_type: str | None = None
    default_days: int | None = None
    feishu_webhook_url: str | None = None
    feishu_push_enabled: bool | None = None


@router.post("/", response_model=UserConfigResponse)
async def create_user_config(
    config: UserConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建用户配置

    API Key会被加密存储
    """
    # 检查是否已存在
    result = await db.execute(
        select(UserConfig).where(UserConfig.user_id == config.user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User config already exists")

    # 加密API Key
    encryption_manager = get_encryption_manager()
    encrypted_openai_key = (
        encryption_manager.encrypt(config.openai_api_key)
        if config.openai_api_key
        else None
    )
    encrypted_anthropic_key = (
        encryption_manager.encrypt(config.anthropic_api_key)
        if config.anthropic_api_key
        else None
    )

    # 创建配置
    user_config = UserConfig(
        user_id=config.user_id,
        openai_api_key=encrypted_openai_key,
        openai_base_url=config.openai_base_url,
        openai_model=config.openai_model,
        anthropic_api_key=encrypted_anthropic_key,
        anthropic_model=config.anthropic_model,
        default_analysis_type=config.default_analysis_type,
        default_days=config.default_days,
    )

    db.add(user_config)
    await db.commit()
    await db.refresh(user_config)

    # 返回时脱敏API Key
    return UserConfigResponse(
        id=user_config.id,
        user_id=user_config.user_id,
        openai_api_key=(
            _mask_api_key(config.openai_api_key) if config.openai_api_key else None
        ),
        openai_base_url=user_config.openai_base_url,
        openai_model=user_config.openai_model,
        anthropic_api_key=(
            _mask_api_key(config.anthropic_api_key)
            if config.anthropic_api_key
            else None
        ),
        anthropic_model=user_config.anthropic_model,
        default_analysis_type=user_config.default_analysis_type,
        default_days=user_config.default_days,
        feishu_webhook_url=user_config.feishu_webhook_url,
        feishu_push_enabled=user_config.feishu_push_enabled,
    )


@router.get("/{user_id}", response_model=UserConfigResponse)
async def get_user_config(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取用户配置"""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user_id))
    user_config = result.scalar_one_or_none()

    if not user_config:
        raise HTTPException(status_code=404, detail="User config not found")

    # 返回时脱敏API Key
    return UserConfigResponse(
        id=user_config.id,
        user_id=user_config.user_id,
        openai_api_key=_mask_encrypted_key(user_config.openai_api_key),
        openai_base_url=user_config.openai_base_url,
        openai_model=user_config.openai_model,
        anthropic_api_key=_mask_encrypted_key(user_config.anthropic_api_key),
        anthropic_model=user_config.anthropic_model,
        default_analysis_type=user_config.default_analysis_type,
        default_days=user_config.default_days,
        feishu_webhook_url=user_config.feishu_webhook_url,
        feishu_push_enabled=user_config.feishu_push_enabled,
    )


@router.put("/{user_id}", response_model=UserConfigResponse)
async def update_user_config(
    user_id: str,
    config: UserConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新用户配置"""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user_id))
    user_config = result.scalar_one_or_none()

    if not user_config:
        raise HTTPException(status_code=404, detail="User config not found")

    # 更新字段
    encryption_manager = get_encryption_manager()

    if config.openai_api_key is not None:
        user_config.openai_api_key = encryption_manager.encrypt(config.openai_api_key)
    if config.openai_base_url is not None:
        user_config.openai_base_url = config.openai_base_url
    if config.openai_model is not None:
        user_config.openai_model = config.openai_model
    if config.anthropic_api_key is not None:
        user_config.anthropic_api_key = encryption_manager.encrypt(
            config.anthropic_api_key
        )
    if config.anthropic_model is not None:
        user_config.anthropic_model = config.anthropic_model
    if config.default_analysis_type is not None:
        user_config.default_analysis_type = config.default_analysis_type
    if config.default_days is not None:
        user_config.default_days = config.default_days
    if config.feishu_webhook_url is not None:
        user_config.feishu_webhook_url = config.feishu_webhook_url
    if config.feishu_push_enabled is not None:
        user_config.feishu_push_enabled = config.feishu_push_enabled

    await db.commit()
    await db.refresh(user_config)

    # 返回时脱敏API Key
    return UserConfigResponse(
        id=user_config.id,
        user_id=user_config.user_id,
        openai_api_key=_mask_encrypted_key(user_config.openai_api_key),
        openai_base_url=user_config.openai_base_url,
        openai_model=user_config.openai_model,
        anthropic_api_key=_mask_encrypted_key(user_config.anthropic_api_key),
        anthropic_model=user_config.anthropic_model,
        default_analysis_type=user_config.default_analysis_type,
        default_days=user_config.default_days,
        feishu_webhook_url=user_config.feishu_webhook_url,
        feishu_push_enabled=user_config.feishu_push_enabled,
    )


def _mask_api_key(key: str) -> str:
    """脱敏API Key"""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _mask_encrypted_key(encrypted_key: str | None) -> str | None:
    """脱敏加密的API Key"""
    if not encrypted_key:
        return None
    # 加密后的key很长，只显示前后各4个字符
    if len(encrypted_key) <= 8:
        return "****"
    return encrypted_key[:4] + "****" + encrypted_key[-4:]
