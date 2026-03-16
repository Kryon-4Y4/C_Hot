"""
外贸数据接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas.trade_data import (
    TradeDataCreate,
    TradeDataUpdate,
    TradeDataResponse,
    TradeDataFilter,
)
from app.services.trade_data_service import TradeDataService
from app.core.security import get_current_user, require_admin

router = APIRouter()


@router.get("", response_model=List[TradeDataResponse])
def get_trade_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    hs_code: Optional[str] = None,
    trade_partner: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(pending|confirmed|rejected)$"),
    sort_by: str = Query("created_at", regex="^(year|hs_code|trade_partner|export_value_usd|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取外贸数据列表
    
    支持筛选条件:
    - year: 年份
    - hs_code: HS编码
    - trade_partner: 贸易伙伴
    - status: 状态 (pending/confirmed/rejected)
    """
    trade_service = TradeDataService(db)
    
    filter_params = TradeDataFilter(
        year=year,
        hs_code=hs_code,
        trade_partner=trade_partner,
        status=status
    )
    
    items, total = trade_service.get_list(
        filter_params=filter_params,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return items


@router.post("", response_model=TradeDataResponse, status_code=status.HTTP_201_CREATED)
def create_trade_data(
    data: TradeDataCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加外贸数据
    """
    trade_service = TradeDataService(db)
    return trade_service.create(data, user_id=current_user.get("user_id"))


@router.post("/bulk")
def bulk_create_trade_data(
    data_list: List[TradeDataCreate],
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    批量添加外贸数据（需要管理员权限）
    """
    trade_service = TradeDataService(db)
    count = trade_service.bulk_create(data_list)
    return {"message": f"成功添加 {count} 条数据"}


@router.get("/{data_id}", response_model=TradeDataResponse)
def get_trade_data_by_id(
    data_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    根据ID获取单条数据
    """
    trade_service = TradeDataService(db)
    data = trade_service.get_by_id(data_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据不存在"
        )
    return data


@router.put("/{data_id}", response_model=TradeDataResponse)
def update_trade_data(
    data_id: int,
    data: TradeDataUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新外贸数据
    """
    trade_service = TradeDataService(db)
    return trade_service.update(data_id, data)


@router.delete("/{data_id}")
def delete_trade_data(
    data_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除外贸数据（需要管理员权限）
    """
    trade_service = TradeDataService(db)
    trade_service.delete(data_id)
    return {"message": "数据删除成功"}


@router.post("/{data_id}/confirm")
def confirm_trade_data(
    data_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认数据（将pending状态转为confirmed）
    """
    trade_service = TradeDataService(db)
    return trade_service.confirm(data_id, current_user.get("user_id"))


@router.get("/statistics/overview")
def get_statistics(
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取统计数据
    
    - year: 指定年份，不指定则统计所有年份
    """
    trade_service = TradeDataService(db)
    return trade_service.get_statistics(year)


@router.get("/statistics/by-year")
def get_statistics_by_year(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    按年份获取统计数据
    """
    from sqlalchemy import func
    from app.models.trade_data import TradeData
    
    results = db.query(
        TradeData.year,
        func.sum(TradeData.export_value_usd).label("total_value"),
        func.count(TradeData.id).label("record_count")
    ).group_by(TradeData.year).order_by(TradeData.year).all()
    
    return [
        {
            "year": r[0],
            "total_value_usd": float(r[1]) if r[1] else 0,
            "record_count": r[2]
        }
        for r in results
    ]
