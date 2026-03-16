"""
爬虫任务模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
import enum

from data_layer.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlerTask(Base):
    """爬虫任务表"""
    __tablename__ = "crawler_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联脚本
    script_id = Column(Integer, ForeignKey("crawler_scripts.id"), nullable=False)
    script_name = Column(String(100), nullable=False)
    
    # 任务状态
    status = Column(String(20), default=TaskStatus.PENDING.value, comment="任务状态")
    
    # 执行信息
    started_at = Column(DateTime(timezone=True), comment="开始时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    duration_seconds = Column(Numeric(10, 2), comment="执行时长(秒)")
    
    # 执行结果
    total_records = Column(Integer, default=0, comment="获取记录数")
    new_records = Column(Integer, default=0, comment="新增记录数")
    updated_records = Column(Integer, default=0, comment="更新记录数")
    error_count = Column(Integer, default=0, comment="错误数")
    
    # 日志和错误
    logs = Column(Text, comment="执行日志")
    error_message = Column(Text, comment="错误信息")
    
    # 触发信息
    triggered_by = Column(Integer, comment="触发用户ID，null表示系统自动")
    trigger_type = Column(String(20), default="manual", comment="触发类型: manual/auto/retry")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CrawlerTask {self.id} {self.status}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "script_id": self.script_id,
            "script_name": self.script_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": float(self.duration_seconds) if self.duration_seconds else None,
            "total_records": self.total_records,
            "new_records": self.new_records,
            "updated_records": self.updated_records,
            "error_count": self.error_count,
            "logs": self.logs,
            "error_message": self.error_message,
            "triggered_by": self.triggered_by,
            "trigger_type": self.trigger_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
