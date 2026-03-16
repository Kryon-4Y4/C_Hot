"""
数据库连接 - 从 data-layer 导入
"""
from data_layer import get_db, SessionLocal

# 导出供其他模块使用
__all__ = ["get_db", "SessionLocal"]
