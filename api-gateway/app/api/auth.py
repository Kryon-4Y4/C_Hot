"""
认证接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, TokenRefreshRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.core.security import get_current_user, decode_token
from data_layer import AuditLog

router = APIRouter()
security = HTTPBearer()


def log_visitor_action(request: Request, action: str, resource_type: str, description: str = None, user_id: int = None, username: str = None):
    """记录访客操作日志"""
    try:
        # 这里需要通过依赖注入获取db，但为了简化，我们直接在需要的地方调用
        pass
    except:
        pass


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    auth_service = AuthService(db)
    result = auth_service.authenticate(credentials, request)
    return result


@router.post("/register", response_model=LoginResponse)
def register(user_data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户注册
    
    - **username**: 用户名
    - **email**: 邮箱
    - **password**: 密码
    - **full_name**: 姓名（可选）
    - **email_subscribed**: 是否订阅邮件（可选）
    """
    auth_service = AuthService(db)
    result = auth_service.register(user_data, request)
    return result


@router.post("/refresh")
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    auth_service = AuthService(db)
    return auth_service.refresh_token(request.refresh_token)


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    用户登出（客户端需要清除令牌）
    """
    return {"message": "登出成功"}


@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    return current_user


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    """
    from app.services.user_service import UserService
    from app.core.security import verify_password, get_password_hash
    
    user_service = UserService(db)
    user = user_service.get_by_id(current_user["user_id"])
    
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@router.post("/subscribe-email")
def subscribe_email(
    subscribe: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    设置邮件订阅
    """
    from data_layer import User
    
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.email_subscribed = subscribe
    db.commit()
    
    return {
        "message": "已订阅邮件通知" if subscribe else "已取消邮件订阅",
        "email_subscribed": subscribe
    }
