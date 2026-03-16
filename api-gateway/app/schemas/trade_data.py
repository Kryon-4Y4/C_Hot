"""
外贸数据Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TradeDataBase(BaseModel):
    """外贸数据基础模型"""
    year: int = Field(..., ge=2000, le=2100, description="年份")
    hs_code: str = Field(..., max_length=20, description="HS编码")
    hs_description: Optional[str] = Field(None, max_length=255, description="HS编码描述")
    trade_partner: str = Field(..., max_length=100, description="贸易伙伴")
    export_quantity: Optional[float] = Field(None, ge=0, description="出口数量")
    quantity_unit: Optional[str] = Field(None, max_length=20, description="数量单位")
    export_value_usd: float = Field(..., ge=0, description="出口金额(美元)")
    unit_value_usd: Optional[float] = Field(None, ge=0, description="单价值(美元)")
    trade_mode: Optional[str] = Field(None, max_length=50, description="贸易方式")
    data_source: Optional[str] = Field("UN Comtrade", max_length=50, description="数据来源")
    notes: Optional[str] = Field(None, description="备注")


class TradeDataCreate(TradeDataBase):
    """创建外贸数据"""
    pass


class TradeDataUpdate(BaseModel):
    """更新外贸数据"""
    year: Optional[int] = Field(None, ge=2000, le=2100)
    hs_code: Optional[str] = Field(None, max_length=20)
    hs_description: Optional[str] = Field(None, max_length=255)
    trade_partner: Optional[str] = Field(None, max_length=100)
    export_quantity: Optional[float] = Field(None, ge=0)
    quantity_unit: Optional[str] = Field(None, max_length=20)
    export_value_usd: Optional[float] = Field(None, ge=0)
    unit_value_usd: Optional[float] = Field(None, ge=0)
    trade_mode: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None)
    status: Optional[str] = Field(None, pattern="^(pending|confirmed|rejected)$")


class TradeDataResponse(TradeDataBase):
    """外贸数据响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: str
    confirmed_by: Optional[int]
    confirmed_at: Optional[datetime]
    crawled_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class TradeDataListResponse(BaseModel):
    """外贸数据列表响应"""
    items: List[TradeDataResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TradeDataFilter(BaseModel):
    """外贸数据筛选条件"""
    year: Optional[int] = None
    hs_code: Optional[str] = None
    trade_partner: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
