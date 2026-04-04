"""
订阅 API
"""

from fastapi import APIRouter, HTTPException, status

from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/subscribe", tags=["订阅"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_subscription():
    """创建订阅"""
    # TODO: 实现订阅逻辑
    return {"status": "created"}


@router.get("/list")
async def list_subscriptions():
    """获取订阅列表"""
    # TODO: 实现列表逻辑
    return {"subscriptions": []}


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: str):
    """删除订阅"""
    # TODO: 实现删除逻辑
    pass
