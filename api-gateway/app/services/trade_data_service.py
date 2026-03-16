"""
外贸数据服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional, Tuple
from fastapi import HTTPException, status

# 从 data-layer 导入模型
from data_layer import TradeData

from app.schemas.trade_data import TradeDataCreate, TradeDataUpdate, TradeDataFilter


class TradeDataService:
    """外贸数据服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, data_id: int) -> Optional[TradeData]:
        """根据ID获取数据"""
        return self.db.query(TradeData).filter(TradeData.id == data_id).first()
    
    def get_list(
        self,
        filter_params: TradeDataFilter,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[TradeData], int]:
        """获取数据列表（支持筛选和分页）"""
        query = self.db.query(TradeData)
        
        # 应用筛选条件
        if filter_params.year:
            query = query.filter(TradeData.year == filter_params.year)
        if filter_params.hs_code:
            query = query.filter(TradeData.hs_code.contains(filter_params.hs_code))
        if filter_params.trade_partner:
            query = query.filter(TradeData.trade_partner.contains(filter_params.trade_partner))
        if filter_params.status:
            query = query.filter(TradeData.status == filter_params.status)
        if filter_params.start_date:
            query = query.filter(TradeData.created_at >= filter_params.start_date)
        if filter_params.end_date:
            query = query.filter(TradeData.created_at <= filter_params.end_date)
        if filter_params.min_value:
            query = query.filter(TradeData.export_value_usd >= filter_params.min_value)
        if filter_params.max_value:
            query = query.filter(TradeData.export_value_usd <= filter_params.max_value)
        
        # 计算总数
        total = query.count()
        
        # 排序
        sort_column = getattr(TradeData, sort_by, TradeData.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    def create(self, data: TradeDataCreate, user_id: Optional[int] = None) -> TradeData:
        """创建数据"""
        db_data = TradeData(
            year=data.year,
            hs_code=data.hs_code,
            hs_description=data.hs_description,
            trade_partner=data.trade_partner,
            export_quantity=data.export_quantity,
            quantity_unit=data.quantity_unit,
            export_value_usd=data.export_value_usd,
            unit_value_usd=data.unit_value_usd,
            trade_mode=data.trade_mode,
            data_source=data.data_source,
            notes=data.notes,
            status="pending" if user_id else "confirmed",
            confirmed_by=user_id if not user_id else None,
        )
        self.db.add(db_data)
        self.db.commit()
        self.db.refresh(db_data)
        return db_data
    
    def update(self, data_id: int, data: TradeDataUpdate) -> TradeData:
        """更新数据"""
        db_data = self.get_by_id(data_id)
        if not db_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_data, field, value)
        
        self.db.commit()
        self.db.refresh(db_data)
        return db_data
    
    def delete(self, data_id: int) -> bool:
        """删除数据"""
        db_data = self.get_by_id(data_id)
        if not db_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        self.db.delete(db_data)
        self.db.commit()
        return True
    
    def confirm(self, data_id: int, user_id: int) -> TradeData:
        """确认数据"""
        db_data = self.get_by_id(data_id)
        if not db_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        db_data.status = "confirmed"
        db_data.confirmed_by = user_id
        from datetime import datetime
        db_data.confirmed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(db_data)
        return db_data
    
    def get_statistics(self, year: Optional[int] = None) -> dict:
        """获取统计数据"""
        query = self.db.query(TradeData)
        if year:
            query = query.filter(TradeData.year == year)
        
        # 基础统计
        total_records = query.count()
        total_value = query.with_entities(
            func.sum(TradeData.export_value_usd)
        ).scalar() or 0
        
        # 按HS编码统计
        hs_stats = query.with_entities(
            TradeData.hs_code,
            func.sum(TradeData.export_value_usd).label("total_value"),
            func.count(TradeData.id).label("count")
        ).group_by(TradeData.hs_code).all()
        
        # 按贸易伙伴统计
        partner_stats = query.with_entities(
            TradeData.trade_partner,
            func.sum(TradeData.export_value_usd).label("total_value"),
            func.count(TradeData.id).label("count")
        ).group_by(TradeData.trade_partner).order_by(
            desc(func.sum(TradeData.export_value_usd))
        ).limit(10).all()
        
        return {
            "total_records": total_records,
            "total_value_usd": float(total_value),
            "hs_statistics": [
                {"hs_code": s[0], "total_value": float(s[1]), "count": s[2]}
                for s in hs_stats
            ],
            "top_partners": [
                {"partner": s[0], "total_value": float(s[1]), "count": s[2]}
                for s in partner_stats
            ]
        }
    
    def bulk_create(self, data_list: List[TradeDataCreate]) -> int:
        """批量创建数据"""
        db_items = []
        for data in data_list:
            db_data = TradeData(
                year=data.year,
                hs_code=data.hs_code,
                hs_description=data.hs_description,
                trade_partner=data.trade_partner,
                export_quantity=data.export_quantity,
                quantity_unit=data.quantity_unit,
                export_value_usd=data.export_value_usd,
                unit_value_usd=data.unit_value_usd,
                trade_mode=data.trade_mode,
                data_source=data.data_source,
                notes=data.notes,
                status="confirmed",
            )
            db_items.append(db_data)
        
        self.db.bulk_save_objects(db_items)
        self.db.commit()
        return len(db_items)
