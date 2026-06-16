"""
数据库连接与会话管理（SQLite + SQLAlchemy）。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# SQLite 需要 check_same_thread=False 以支持多线程访问
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖：获取数据库会话并在请求结束后关闭."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表（首次运行时调用）."""
    Base.metadata.create_all(bind=engine)
