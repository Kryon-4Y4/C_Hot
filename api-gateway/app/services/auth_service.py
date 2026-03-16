"""
认证服务
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

# 从 data-layer 导入模型
from data_layer import User

from app.schemas.auth import LoginRequest
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.services.user_service import UserService


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def authenticate(self, credentials: LoginRequest) -> dict:
        """用户认证"""
        # 查找用户
        user = self.user_service.get_by_username(credentials.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )
        
        # 验证密码
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 更新最后登录时间
        self.user_service.update_last_login(user.id)
        
        # 生成令牌
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30分钟
            "user": user.to_dict()
        }
    
    def refresh_token(self, refresh_token: str) -> dict:
        """刷新访问令牌"""
        from app.core.security import decode_token
        
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        username = payload.get("sub")
        user = self.user_service.get_by_username(username)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 生成新的访问令牌
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        }
        
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
