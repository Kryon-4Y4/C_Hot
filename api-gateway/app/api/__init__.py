from fastapi import APIRouter
from app.api import auth, users, trade_data, crawler, system

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(trade_data.router, prefix="/trade-data", tags=["外贸数据"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["爬虫管理"])
api_router.include_router(system.router, prefix="/system", tags=["系统"])
