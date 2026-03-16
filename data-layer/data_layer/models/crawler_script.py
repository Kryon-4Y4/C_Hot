"""
爬虫脚本模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from data_layer.database import Base


class CrawlerScript(Base):
    """爬虫脚本表"""
    __tablename__ = "crawler_scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="脚本名称")
    description = Column(Text, comment="脚本描述")
    
    # 代码内容
    code = Column(Text, nullable=False, comment="Python代码")
    
    # 配置
    hs_codes = Column(String(500), comment="HS编码列表，逗号分隔")
    periods = Column(String(200), comment="查询年份列表，逗号分隔")
    partners = Column(Text, comment="贸易伙伴JSON配置")
    
    # 执行配置
    is_active = Column(Boolean, default=True, comment="是否启用")
    auto_run = Column(Boolean, default=False, comment="是否自动运行")
    cron_expression = Column(String(50), comment="定时表达式")
    
    # 元数据
    version = Column(String(20), default="1.0.0", comment="版本号")
    created_by = Column(Integer, comment="创建用户ID")
    updated_by = Column(Integer, comment="更新用户ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CrawlerScript {self.name}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "hs_codes": self.hs_codes,
            "periods": self.periods,
            "partners": self.partners,
            "is_active": self.is_active,
            "auto_run": self.auto_run,
            "cron_expression": self.cron_expression,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
