"""
系统接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis
import platform
import psutil
from datetime import datetime

from app.database import get_db, engine
from app.core.config import settings
from app.core.security import get_current_user, require_admin

router = APIRouter()

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/health")
def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/stats")
def get_system_stats(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取系统统计信息（需要管理员权限）
    """
    # 数据库统计
    from sqlalchemy import func
    from app.models.trade_data import TradeData
    from app.models.user import User
    from app.models.crawler_task import CrawlerTask
    
    db_stats = {
        "trade_data_count": db.query(TradeData).count(),
        "user_count": db.query(User).count(),
        "crawler_task_count": db.query(CrawlerTask).count(),
    }
    
    # Redis统计
    try:
        redis_info = redis_client.info()
        redis_stats = {
            "connected": True,
            "used_memory_human": redis_info.get("used_memory_human"),
            "connected_clients": redis_info.get("connected_clients"),
            "total_commands_processed": redis_info.get("total_commands_processed"),
        }
    except Exception as e:
        redis_stats = {"connected": False, "error": str(e)}
    
    # 系统资源
    system_stats = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent,
        }
    }
    
    return {
        "database": db_stats,
        "redis": redis_stats,
        "system": system_stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info")
def get_system_info():
    """
    获取系统信息
    """
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }
