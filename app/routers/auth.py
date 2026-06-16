"""
认证路由：注册、登录、刷新 Token、登出。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshRequest,
    MessageResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_token,
    decode_token,
)
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """用户注册 — 成功后直接返回 Token，免去二次登录."""
    user = register_user(db, data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已被注册",
        )
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """用户登录 — 支持用户名或邮箱."""
    user = authenticate_user(db, data.login, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
        )
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshRequest):
    """使用 Refresh Token 获取新的 Access Token."""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期",
        )
    user_id = int(payload.get("sub"))
    access_token = create_token(user_id, "access")
    refresh_token = create_token(user_id, "refresh")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    """登出 — 前端清除 Token 即可，后端为无状态 JWT，无需额外操作."""
    return MessageResponse(message="已登出，请清除本地 Token")
