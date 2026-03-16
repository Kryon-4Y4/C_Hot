"""
爬虫服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from fastapi import HTTPException, status

# 从 data-layer 导入模型
from data_layer import CrawlerScript, CrawlerTask, TaskStatus

from app.schemas.crawler_script import CrawlerScriptCreate, CrawlerScriptUpdate
from app.schemas.crawler_task import CrawlerTaskCreate


class CrawlerService:
    """爬虫服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== 爬虫脚本管理 ==========
    
    def get_script_by_id(self, script_id: int) -> Optional[CrawlerScript]:
        """根据ID获取脚本"""
        return self.db.query(CrawlerScript).filter(CrawlerScript.id == script_id).first()
    
    def get_script_by_name(self, name: str) -> Optional[CrawlerScript]:
        """根据名称获取脚本"""
        return self.db.query(CrawlerScript).filter(CrawlerScript.name == name).first()
    
    def get_scripts_list(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple[List[CrawlerScript], int]:
        """获取脚本列表"""
        query = self.db.query(CrawlerScript)
        
        if is_active is not None:
            query = query.filter(CrawlerScript.is_active == is_active)
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return items, total
    
    def create_script(
        self,
        data: CrawlerScriptCreate,
        created_by: Optional[int] = None
    ) -> CrawlerScript:
        """创建脚本"""
        # 检查名称是否已存在
        if self.get_script_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="脚本名称已存在"
            )
        
        db_script = CrawlerScript(
            name=data.name,
            description=data.description,
            code=data.code,
            hs_codes=data.hs_codes,
            periods=data.periods,
            partners=data.partners,
            is_active=data.is_active,
            auto_run=data.auto_run,
            cron_expression=data.cron_expression,
            version=data.version,
            created_by=created_by,
        )
        self.db.add(db_script)
        self.db.commit()
        self.db.refresh(db_script)
        return db_script
    
    def update_script(
        self,
        script_id: int,
        data: CrawlerScriptUpdate,
        updated_by: Optional[int] = None
    ) -> CrawlerScript:
        """更新脚本"""
        db_script = self.get_script_by_id(script_id)
        if not db_script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="脚本不存在"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 检查新名称是否与其他脚本冲突
        if "name" in update_data and update_data["name"] != db_script.name:
            if self.get_script_by_name(update_data["name"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="脚本名称已存在"
                )
        
        for field, value in update_data.items():
            if value is not None:
                setattr(db_script, field, value)
        
        db_script.updated_by = updated_by
        self.db.commit()
        self.db.refresh(db_script)
        return db_script
    
    def delete_script(self, script_id: int) -> bool:
        """删除脚本"""
        db_script = self.get_script_by_id(script_id)
        if not db_script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="脚本不存在"
            )
        
        self.db.delete(db_script)
        self.db.commit()
        return True
    
    # ========== 爬虫任务管理 ==========
    
    def get_task_by_id(self, task_id: int) -> Optional[CrawlerTask]:
        """根据ID获取任务"""
        return self.db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    
    def get_tasks_list(
        self,
        page: int = 1,
        page_size: int = 20,
        script_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> tuple[List[CrawlerTask], int]:
        """获取任务列表"""
        query = self.db.query(CrawlerTask)
        
        if script_id:
            query = query.filter(CrawlerTask.script_id == script_id)
        if status:
            query = query.filter(CrawlerTask.status == status)
        
        total = query.count()
        items = query.order_by(desc(CrawlerTask.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return items, total
    
    def create_task(self, data: CrawlerTaskCreate) -> CrawlerTask:
        """创建任务"""
        db_task = CrawlerTask(
            script_id=data.script_id,
            script_name=data.script_name,
            status=TaskStatus.PENDING.value,
            triggered_by=data.triggered_by,
            trigger_type=data.trigger_type,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def update_task_status(
        self,
        task_id: int,
        status: str,
        logs: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs
    ) -> CrawlerTask:
        """更新任务状态"""
        db_task = self.get_task_by_id(task_id)
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        db_task.status = status
        if logs:
            db_task.logs = logs
        if error_message:
            db_task.error_message = error_message
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(db_task, key):
                setattr(db_task, key, value)
        
        # 设置完成时间
        if status in [TaskStatus.SUCCESS.value, TaskStatus.FAILED.value]:
            from datetime import datetime
            db_task.completed_at = datetime.now()
            if db_task.started_at:
                duration = (db_task.completed_at - db_task.started_at).total_seconds()
                db_task.duration_seconds = duration
        
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def get_running_tasks(self) -> List[CrawlerTask]:
        """获取正在运行的任务"""
        return self.db.query(CrawlerTask).filter(
            CrawlerTask.status == TaskStatus.RUNNING.value
        ).all()
