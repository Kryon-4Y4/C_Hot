"""
认证接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, TokenRefreshRequest
from app.services.auth_service import AuthService
from app.core.security import get_current_user, decode_token

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    auth_service = AuthService(db)
    result = auth_service.authenticate(credentials)
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
