"""
审计日志模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from data_layer.database import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 操作信息
    action = Column(String(50), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(String(50), comment="资源ID")
    
    # 用户信息
    user_id = Column(Integer, comment="用户ID")
    username = Column(String(50), comment="用户名")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    
    # 变更详情
    old_values = Column(JSON, comment="变更前值")
    new_values = Column(JSON, comment="变更后值")
    description = Column(Text, comment="操作描述")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
