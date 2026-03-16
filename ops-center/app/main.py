"""
运维中心 - FastAPI
提供系统监控、日志查看、运维操作等功能
"""
import os
import psutil
import platform
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
import redis

# 从 data-layer 导入
from data_layer import engine

app = FastAPI(
    title="运维中心",
    description="手机维修配件外贸数据系统运维管理",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/phone_parts_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://api-gateway:8000')

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_total: int
    memory_used: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    network_io: Dict[str, int]


@app.get("/")
def root():
    return {"name": "运维中心", "version": "1.0.0"}


@app.get("/health", response_model=HealthStatus)
def health_check():
    """健康检查 - 检查所有服务状态"""
    services = {}
    
    # 检查数据库
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        services['database'] = 'healthy'
    except Exception as e:
        services['database'] = f'unhealthy: {str(e)}'
    
    # 检查Redis
    try:
        redis_client.ping()
        services['redis'] = 'healthy'
    except Exception as e:
        services['redis'] = f'unhealthy: {str(e)}'
    
    # 检查API网关
    try:
        import requests
        response = requests.get(f"{API_GATEWAY_URL}/system/health", timeout=5)
        if response.status_code == 200:
            services['api_gateway'] = 'healthy'
        else:
            services['api_gateway'] = f'unhealthy: status {response.status_code}'
    except Exception as e:
        services['api_gateway'] = f'unhealthy: {str(e)}'
    
    overall_status = 'healthy' if all(s == 'healthy' for s in services.values()) else 'degraded'
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": services
    }


@app.get("/metrics", response_model=SystemMetrics)
def get_system_metrics():
    """获取系统指标"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()
    
    return {
        "cpu_percent": cpu_percent,
        "memory_total": memory.total,
        "memory_used": memory.used,
        "memory_percent": memory.percent,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_percent": disk.percent,
        "network_io": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        }
    }


@app.get("/database/stats")
def get_database_stats():
    """获取数据库统计信息"""
    try:
        with engine.connect() as conn:
            stats = {}
            
            tables = ['users', 'trade_data', 'crawler_scripts', 'crawler_tasks', 'audit_logs']
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[table] = result.scalar()
                except:
                    stats[table] = 0
            
            result = conn.execute(text("""
                SELECT status, COUNT(*) as count 
                FROM crawler_tasks 
                GROUP BY status
            """))
            task_stats = {row[0]: row[1] for row in result}
            
            return {
                "table_counts": stats,
                "task_status": task_stats
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@app.post("/cache/clear")
def clear_cache():
    """清除Redis缓存"""
    try:
        redis_client.flushall()
        return {"message": "缓存清除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@app.get("/cache/stats")
def get_cache_stats():
    """获取Redis缓存统计"""
    try:
        info = redis_client.info()
        return {
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
