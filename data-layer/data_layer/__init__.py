"""
data-layer: 共享数据访问层

提供统一的数据库连接、模型定义和基础数据操作
"""

from data_layer.database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    init_db,
)
from data_layer.models import (
    User,
    UserRole,
    TradeData,
    CrawlerScript,
    CrawlerTask,
    TaskStatus,
    AuditLog,
)

__version__ = "1.0.0"

__all__ = [
    # 数据库
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    # 模型
    "User",
    "UserRole",
    "TradeData",
    "CrawlerScript",
    "CrawlerTask",
    "TaskStatus",
    "AuditLog",
]
