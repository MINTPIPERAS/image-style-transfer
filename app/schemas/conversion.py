"""
转换记录相关 Pydantic 校验模型。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversionRecordOut(BaseModel):
    """转换记录响应."""
    id: int
    original_filename: str
    style_type: str
    original_size: int
    result_size: int
    status: str
    created_at: Optional[datetime] = None
    result_url: str = ""       # 前端可直接加载的结果图 URL
    original_url: str = ""     # 前端可直接加载的原图 URL

    class Config:
        from_attributes = True


class ConversionListResponse(BaseModel):
    """转换记录分页响应."""
    items: list[ConversionRecordOut]
    total: int
    page: int
    page_size: int
