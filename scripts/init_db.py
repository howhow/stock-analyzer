#!/usr/bin/env python3
"""
数据库初始化脚本

创建数据库表结构，初始化基础数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine  # noqa: E402

from app.models.base import Base  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402
from config import settings  # noqa: E402

logger = get_logger(__name__)


def init_database() -> None:
    """
    初始化数据库

    创建所有表结构
    """
    logger.info("开始初始化数据库...")

    # 创建数据库引擎
    engine = create_engine(
        settings.database_url,
        echo=True,  # 打印 SQL 语句，便于调试
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    logger.info("数据库初始化完成")


def main() -> None:
    """主函数"""
    try:
        init_database()
        print("✅ 数据库初始化成功")
    except Exception as e:
        logger.error("数据库初始化失败", error=str(e))
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
