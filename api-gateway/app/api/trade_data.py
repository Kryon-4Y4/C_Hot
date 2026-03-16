"""
外贸数据接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
from app.core.security import get_current_user
from data_layer import AuditLog

router = APIRouter()


def log_visitor_query(db: Session, request: Request, filters: dict, user: dict = None):
    """记录访客查询日志"""
    try:
        description = f"查询外贸数据"
        if filters.get('year'):
            description += f", 年份: {filters['year']}"
        if filters.get('hs_code'):
            description += f", HS编码: {filters['hs_code']}"
        if filters.get('trade_partner'):
            description += f", 贸易伙伴: {filters['trade_partner']}"
        
        audit_log = AuditLog(
            action='query_trade_data',
            resource_type='trade_data',
            username=user.get('username') if user else None,
            user_id=user.get('user_id') if user else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent', ''),
            description=description
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"记录查询日志失败: {e}")


@router.get("")
def get_trade_data(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    hs_code: Optional[str] = None,
    trade_partner: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(pending|confirmed|rejected)$"),
    sort_by: str = Query("created_at", regex="^(year|hs_code|trade_partner|export_value_usd|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    获取外贸数据列表（公开接口，无需认证）
    
    支持筛选条件:
    - year: 年份
    - hs_code: HS编码
    - trade_partner: 贸易伙伴
    - status: 状态 (pending/confirmed/rejected)
    
    返回: {items: 数据列表, total: 总数}
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
    
    # 记录访客查询日志
    log_visitor_query(db, request, {
        'year': year,
        'hs_code': hs_code,
        'trade_partner': trade_partner,
        'status': status
    })
    
    # 转换为字典列表
    items_dict = []
    for item in items:
        items_dict.append({
            "id": item.id,
            "year": item.year,
            "hs_code": item.hs_code,
            "hs_description": item.hs_description,
            "trade_partner": item.trade_partner,
            "export_quantity": item.export_quantity,
            "quantity_unit": item.quantity_unit,
            "export_value_usd": item.export_value_usd,
            "unit_value_usd": item.unit_value_usd,
            "trade_mode": item.trade_mode,
            "data_source": item.data_source,
            "notes": item.notes,
            "status": item.status,
            "confirmed_by": item.confirmed_by,
            "confirmed_at": item.confirmed_at.isoformat() if item.confirmed_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        })
    
    return {"items": items_dict, "total": total}


@router.post("", response_model=TradeDataResponse, status_code=status.HTTP_201_CREATED)
def create_trade_data(
    data: TradeDataCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加外贸数据（需要认证）
    """
    trade_service = TradeDataService(db)
    return trade_service.create(data, user_id=current_user.get("user_id"))


@router.post("/bulk")
def bulk_create_trade_data(
    data_list: List[TradeDataCreate],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量添加外贸数据（需要管理员权限）
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    trade_service = TradeDataService(db)
    count = trade_service.bulk_create(data_list)
    return {"message": f"成功添加 {count} 条数据"}


@router.get("/{data_id}", response_model=TradeDataResponse)
def get_trade_data_by_id(
    data_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    根据ID获取单条数据（公开接口，无需认证）
    """
    trade_service = TradeDataService(db)
    data = trade_service.get_by_id(data_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据不存在"
        )
    
    # 记录查看日志
    try:
        audit_log = AuditLog(
            action='view_trade_data',
            resource_type='trade_data',
            resource_id=str(data_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent', ''),
            description=f'查看数据详情: ID {data_id}'
        )
        db.add(audit_log)
        db.commit()
    except:
        db.rollback()
    
    return data


@router.put("/{data_id}", response_model=TradeDataResponse)
def update_trade_data(
    data_id: int,
    data: TradeDataUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新外贸数据（需要认证）
    """
    trade_service = TradeDataService(db)
    return trade_service.update(data_id, data)


@router.delete("/{data_id}")
def delete_trade_data(
    data_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除外贸数据（需要管理员权限）
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
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
    确认数据（将pending状态转为confirmed，需要认证）
    """
    trade_service = TradeDataService(db)
    return trade_service.confirm(data_id, current_user.get("user_id"))


@router.get("/statistics/overview")
def get_statistics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取统计数据（公开接口，无需认证）
    
    - year: 指定年份，不指定则统计所有年份
    """
    trade_service = TradeDataService(db)
    return trade_service.get_statistics(year)


@router.get("/statistics/by-year")
def get_statistics_by_year(
    db: Session = Depends(get_db)
):
    """
    按年份获取统计数据（公开接口，无需认证）
    """
    from sqlalchemy import func
    from data_layer import TradeData
    
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
