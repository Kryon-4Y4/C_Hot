"""
用户管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_user, require_admin

router = APIRouter()


@router.get("", response_model=List[UserResponse])
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（需要管理员权限）
    """
    user_service = UserService(db)
    items, total = user_service.get_list(page=page, page_size=page_size, role=role, is_active=is_active)
    
    # 添加响应头中的总数信息
    return items


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建用户（需要管理员权限）
    """
    user_service = UserService(db)
    return user_service.create(user_data, created_by=current_user.get("user_id"))


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    """
    user_service = UserService(db)
    user = user_service.get_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取指定用户信息（需要管理员权限）
    """
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（需要管理员权限）
    """
    user_service = UserService(db)
    return user_service.update(user_id, user_data, updated_by=current_user.get("user_id"))


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户（需要管理员权限）
    """
    user_service = UserService(db)
    user_service.delete(user_id)
    return {"message": "用户删除成功"}
