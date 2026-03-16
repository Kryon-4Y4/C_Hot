"""
认证服务
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from datetime import datetime

# 从 data-layer 导入模型
from data_layer import User, AuditLog

from app.schemas.auth import LoginRequest, RegisterRequest
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from app.services.user_service import UserService


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def _log_action(self, request: Request, action: str, resource_type: str, 
                    description: str = None, user_id: int = None, username: str = None):
        """记录操作日志"""
        try:
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                username=username,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent', ''),
                description=description
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"记录日志失败: {e}")
    
    def authenticate(self, credentials: LoginRequest, request: Request = None) -> dict:
        """用户认证"""
        # 查找用户
        user = self.user_service.get_by_username(credentials.username)
        if not user:
            # 记录失败日志
            if request:
                self._log_action(request, 'login_failed', 'auth', 
                               f'用户名不存在: {credentials.username}', username=credentials.username)
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
            # 记录失败日志
            if request:
                self._log_action(request, 'login_failed', 'auth', 
                               f'密码错误: {credentials.username}', username=credentials.username)
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
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # 记录成功日志
        if request:
            self._log_action(request, 'login_success', 'auth', 
                           f'用户登录: {user.username}', user_id=user.id, username=user.username)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30分钟
            "user": user.to_dict()
        }
    
    def register(self, user_data: RegisterRequest, request: Request = None) -> dict:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = self.user_service.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建新用户
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name or user_data.username,
            role='user',
            is_active=True,
            email_subscribed=user_data.email_subscribed if user_data.email_subscribed is not None else False
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        # 记录注册日志
        if request:
            self._log_action(request, 'register', 'user', 
                           f'新用户注册: {new_user.username}', user_id=new_user.id, username=new_user.username)
        
        # 生成令牌
        token_data = {
            "sub": new_user.username,
            "user_id": new_user.id,
            "role": new_user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": new_user.to_dict()
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
            "role": user.role
        }
        
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
