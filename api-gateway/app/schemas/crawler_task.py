"""
爬虫任务Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlerTaskBase(BaseModel):
    """爬虫任务基础模型"""
    script_id: int = Field(..., description="脚本ID")
    script_name: str = Field(..., description="脚本名称")
    status: str = Field("pending", description="任务状态")
    trigger_type: str = Field("manual", description="触发类型")


class CrawlerTaskCreate(CrawlerTaskBase):
    """创建爬虫任务"""
    triggered_by: Optional[int] = Field(None, description="触发用户ID")


class CrawlerTaskResponse(CrawlerTaskBase):
    """爬虫任务响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_records: int
    new_records: int
    updated_records: int
    error_count: int
    logs: Optional[str]
    error_message: Optional[str]
    triggered_by: Optional[int]
    created_at: datetime


class CrawlerTaskListResponse(BaseModel):
    """爬虫任务列表响应"""
    items: List[CrawlerTaskResponse]
    total: int
    page: int
    page_size: int


class TriggerCrawlerRequest(BaseModel):
    """触发爬虫请求"""
    script_id: int = Field(..., description="脚本ID")
    params: Optional[dict] = Field(None, description="执行参数")


class TriggerCrawlerResponse(BaseModel):
    """触发爬虫响应"""
    task_id: int
    message: str
