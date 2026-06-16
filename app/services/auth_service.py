"""
认证服务：密码哈希与 JWT 生成/验证。
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE
from app.models.user import User
from app.schemas.user import UserRegister


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希，返回加密后的字符串."""
    # bcrypt 要求密码不超过 72 字节
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配."""
    plain_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_token(user_id: int, token_type: str = "access") -> str:
    """创建 JWT Token."""
    if token_type == "access":
        expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE
    else:
        expire = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码并验证 JWT Token，失败返回 None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def register_user(db: Session, data: UserRegister) -> User | None:
    """注册新用户，用户名或邮箱重复则返回 None."""
    # 检查重复
    if db.query(User).filter(User.username == data.username).first():
        return None
    if db.query(User).filter(User.email == data.email).first():
        return None

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login: str, password: str) -> User | None:
    """使用用户名或邮箱 + 密码认证用户."""
    user = db.query(User).filter(
        (User.username == login) | (User.email == login)
    ).first()

    if user and verify_password(password, user.password_hash):
        return user
    return None
