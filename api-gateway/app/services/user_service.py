"""
用户服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status

# 从 data-layer 导入模型
from data_layer import User, UserRole

from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return items, total
    
    def create(self, data: UserCreate, created_by: Optional[int] = None) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if self.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if self.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        db_user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role if isinstance(data.role, UserRole) else UserRole(data.role),
            is_active=data.is_active,
            is_superuser=data.role == UserRole.ADMIN,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, data: UserUpdate, updated_by: Optional[int] = None) -> User:
        """更新用户"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 处理密码更新
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = get_password_hash(update_data.pop("password"))
        
        # 处理角色更新
        if "role" in update_data and update_data["role"]:
            db_user.role = UserRole(update_data["role"])
        
        # 更新其他字段
        for field, value in update_data.items():
            if value is not None and field != "role":
                setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int) -> bool:
        """删除用户"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不允许删除超级管理员
        if db_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能删除超级管理员"
            )
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        db_user = self.get_by_id(user_id)
        if db_user:
            from datetime import datetime
            db_user.last_login = datetime.now()
            self.db.commit()
