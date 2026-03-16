"""
爬虫脚本Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CrawlerScriptBase(BaseModel):
    """爬虫脚本基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="脚本名称")
    description: Optional[str] = Field(None, description="脚本描述")
    code: str = Field(..., description="Python代码")
    hs_codes: Optional[str] = Field(None, max_length=500, description="HS编码列表")
    periods: Optional[str] = Field(None, max_length=200, description="查询年份")
    partners: Optional[str] = Field(None, description="贸易伙伴JSON")
    is_active: bool = Field(True, description="是否启用")
    auto_run: bool = Field(False, description="是否自动运行")
    cron_expression: Optional[str] = Field(None, max_length=50, description="定时表达式")
    version: str = Field("1.0.0", max_length=20, description="版本号")


class CrawlerScriptCreate(CrawlerScriptBase):
    """创建爬虫脚本"""
    pass


class CrawlerScriptUpdate(BaseModel):
    """更新爬虫脚本"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    code: Optional[str] = None
    hs_codes: Optional[str] = Field(None, max_length=500)
    periods: Optional[str] = Field(None, max_length=200)
    partners: Optional[str] = None
    is_active: Optional[bool] = None
    auto_run: Optional[bool] = None
    cron_expression: Optional[str] = Field(None, max_length=50)
    version: Optional[str] = Field(None, max_length=20)


class CrawlerScriptResponse(CrawlerScriptBase):
    """爬虫脚本响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class CrawlerScriptListResponse(BaseModel):
    """爬虫脚本列表响应"""
    items: List[CrawlerScriptResponse]
    total: int
