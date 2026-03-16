"""
爬虫管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import redis
import json

from app.database import get_db
from app.schemas.crawler_script import (
    CrawlerScriptCreate,
    CrawlerScriptUpdate,
    CrawlerScriptResponse,
)
from app.schemas.crawler_task import (
    CrawlerTaskCreate,
    CrawlerTaskResponse,
    TriggerCrawlerRequest,
    TriggerCrawlerResponse,
)
from app.services.crawler_service import CrawlerService
from app.core.security import get_current_user, require_admin
from app.core.config import settings

router = APIRouter()

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# ========== 爬虫脚本接口 ==========

@router.get("/scripts", response_model=List[CrawlerScriptResponse])
def get_crawler_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取爬虫脚本列表
    """
    crawler_service = CrawlerService(db)
    items, total = crawler_service.get_scripts_list(
        page=page, page_size=page_size, is_active=is_active
    )
    return items


@router.post("/scripts", response_model=CrawlerScriptResponse, status_code=status.HTTP_201_CREATED)
def create_crawler_script(
    data: CrawlerScriptCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建爬虫脚本（需要管理员权限）
    """
    crawler_service = CrawlerService(db)
    return crawler_service.create_script(data, created_by=current_user.get("user_id"))


@router.get("/scripts/{script_id}", response_model=CrawlerScriptResponse)
def get_crawler_script(
    script_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个爬虫脚本
    """
    crawler_service = CrawlerService(db)
    script = crawler_service.get_script_by_id(script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="脚本不存在"
        )
    return script


@router.put("/scripts/{script_id}", response_model=CrawlerScriptResponse)
def update_crawler_script(
    script_id: int,
    data: CrawlerScriptUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新爬虫脚本（需要管理员权限）
    """
    crawler_service = CrawlerService(db)
    return crawler_service.update_script(
        script_id, data, updated_by=current_user.get("user_id")
    )


@router.delete("/scripts/{script_id}")
def delete_crawler_script(
    script_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除爬虫脚本（需要管理员权限）
    """
    crawler_service = CrawlerService(db)
    crawler_service.delete_script(script_id)
    return {"message": "脚本删除成功"}


# ========== 爬虫任务接口 ==========

@router.get("/tasks", response_model=List[CrawlerTaskResponse])
def get_crawler_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    script_id: Optional[int] = None,
    status: Optional[str] = Query(None, regex="^(pending|running|success|failed|cancelled)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取爬虫任务列表
    """
    crawler_service = CrawlerService(db)
    items, total = crawler_service.get_tasks_list(
        page=page, page_size=page_size, script_id=script_id, status=status
    )
    return items


@router.get("/tasks/{task_id}", response_model=CrawlerTaskResponse)
def get_crawler_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个爬虫任务
    """
    crawler_service = CrawlerService(db)
    task = crawler_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


@router.post("/trigger", response_model=TriggerCrawlerResponse)
def trigger_crawler(
    request: TriggerCrawlerRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    触发爬虫任务（需要管理员权限）
    
    将任务发送到Redis队列，由调度服务执行
    """
    crawler_service = CrawlerService(db)
    
    # 检查脚本是否存在
    script = crawler_service.get_script_by_id(request.script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="脚本不存在"
        )
    
    if not script.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="脚本已禁用"
        )
    
    # 创建任务记录
    task_data = CrawlerTaskCreate(
        script_id=script.id,
        script_name=script.name,
        triggered_by=current_user.get("user_id"),
        trigger_type="manual"
    )
    task = crawler_service.create_task(task_data)
    
    # 发送到Redis队列
    task_message = {
        "task_id": task.id,
        "script_id": script.id,
        "script_name": script.name,
        "script_code": script.code,
        "hs_codes": script.hs_codes,
        "periods": script.periods,
        "partners": script.partners,
        "triggered_by": current_user.get("user_id"),
        "params": request.params or {}
    }
    
    redis_client.lpush("crawler_tasks", json.dumps(task_message))
    
    return {
        "task_id": task.id,
        "message": f"爬虫任务已创建，任务ID: {task.id}"
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_crawler_task(
    task_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    取消爬虫任务（需要管理员权限）
    """
    crawler_service = CrawlerService(db)
    
    task = crawler_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消待执行或运行中的任务"
        )
    
    crawler_service.update_task_status(task_id, "cancelled")
    
    return {"message": "任务已取消"}
