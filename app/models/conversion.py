"""
转换记录模型 — 对应 PRD 7.2 conversion_records 表。
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func

from app.database import Base


class ConversionRecord(Base):
    __tablename__ = "conversion_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    result_filename = Column(String(255), nullable=False)
    result_path = Column(String(500), nullable=False)
    style_type = Column(String(50), nullable=False, default="custom")
    original_size = Column(Integer, nullable=False, default=0)
    result_size = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="completed")  # pending, processing, completed, failed
    created_at = Column(DateTime, server_default=func.now())
    is_deleted = Column(Boolean, default=False)
