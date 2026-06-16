"""
用户相关 Pydantic 数据校验模型。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegister(BaseModel):
    """用户注册请求."""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., max_length=100, description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_一-鿿]+$", v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v


class UserLogin(BaseModel):
    """用户登录请求 — 支持用户名或邮箱."""
    login: str = Field(..., min_length=2, max_length=100, description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class TokenResponse(BaseModel):
    """JWT Token 响应."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新 Token 请求."""
    refresh_token: str


class UserProfile(BaseModel):
    """用户个人信息."""
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


class MessageResponse(BaseModel):
    """通用消息响应."""
    message: str
