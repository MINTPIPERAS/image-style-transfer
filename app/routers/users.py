"""
用户路由：个人信息查看、修改密码。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfile, ChangePasswordRequest, MessageResponse
from app.services.auth_service import verify_password, hash_password

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的个人信息."""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
    )


@router.put("/me/password", response_model=MessageResponse)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码 — 需验证旧密码."""
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return MessageResponse(message="密码修改成功")
