"""
外贸数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func

from data_layer.database import Base


class TradeData(Base):
    """外贸出货数据表"""
    __tablename__ = "trade_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基础信息
    year = Column(Integer, nullable=False, index=True, comment="年份")
    hs_code = Column(String(20), nullable=False, index=True, comment="HS编码")
    hs_description = Column(String(255), comment="HS编码描述")
    
    # 贸易信息
    trade_partner = Column(String(100), nullable=False, index=True, comment="贸易伙伴")
    export_quantity = Column(Numeric(20, 4), comment="出口数量")
    quantity_unit = Column(String(20), comment="数量单位")
    export_value_usd = Column(Numeric(20, 2), nullable=False, comment="出口金额(美元)")
    unit_value_usd = Column(Numeric(20, 4), comment="单价值(美元)")
    
    # 补充信息
    trade_mode = Column(String(50), comment="贸易方式")
    data_source = Column(String(50), default="UN Comtrade", comment="数据来源")
    
    # 状态管理
    status = Column(String(20), default="confirmed", comment="状态: pending/confirmed/rejected")
    confirmed_by = Column(Integer, comment="确认用户ID")
    confirmed_at = Column(DateTime(timezone=True), comment="确认时间")
    
    # 元数据
    notes = Column(Text, comment="备注")
    crawled_at = Column(DateTime(timezone=True), comment="抓取时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TradeData {self.year} {self.hs_code} {self.trade_partner}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "year": self.year,
            "hs_code": self.hs_code,
            "hs_description": self.hs_description,
            "trade_partner": self.trade_partner,
            "export_quantity": float(self.export_quantity) if self.export_quantity else None,
            "quantity_unit": self.quantity_unit,
            "export_value_usd": float(self.export_value_usd) if self.export_value_usd else None,
            "unit_value_usd": float(self.unit_value_usd) if self.unit_value_usd else None,
            "trade_mode": self.trade_mode,
            "data_source": self.data_source,
            "status": self.status,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "notes": self.notes,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
