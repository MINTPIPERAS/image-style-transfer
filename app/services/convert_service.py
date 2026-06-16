"""
转换服务：文件存储管理 + 记录 CRUD。
"""
import uuid
import shutil
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import STORAGE_DIR
from app.models.conversion import ConversionRecord


def get_user_storage_dir(user_id: int) -> Path:
    """获取用户隔离的存储目录，不存在则创建."""
    user_dir = Path(STORAGE_DIR) / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def save_uploaded_file(user_id: int, file_bytes: bytes, original_filename: str) -> tuple[Path, str]:
    """
    保存用户上传的文件到隔离目录。
    返回: (文件完整路径, 存储文件名)
    """
    user_dir = get_user_storage_dir(user_id)
    # UUID 前缀避免文件名冲突
    stored_name = f"{uuid.uuid4().hex[:8]}_{original_filename}"
    file_path = user_dir / stored_name
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path, stored_name


def create_conversion_record(
    db: Session,
    user_id: int,
    original_filename: str,
    original_path: str,
    result_filename: str,
    result_path: str,
    style_type: str = "custom",
    original_size: int = 0,
    result_size: int = 0,
    status: str = "completed",
) -> ConversionRecord:
    """创建一条转换记录."""
    record = ConversionRecord(
        user_id=user_id,
        original_filename=original_filename,
        original_path=original_path,
        result_filename=result_filename,
        result_path=result_path,
        style_type=style_type,
        original_size=original_size,
        result_size=result_size,
        status=status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_records(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[ConversionRecord], int]:
    """分页获取用户的转换记录（按时间倒序，排除已软删除的）."""
    query = db.query(ConversionRecord).filter(
        ConversionRecord.user_id == user_id,
        ConversionRecord.is_deleted == False,
    )
    total = query.count()
    records = (
        query
        .order_by(ConversionRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def soft_delete_record(db: Session, record_id: int, user_id: int) -> bool:
    """软删除一条转换记录（仅允许删除自己的记录）。返回是否成功."""
    record = db.query(ConversionRecord).filter(
        ConversionRecord.id == record_id,
        ConversionRecord.user_id == user_id,
        ConversionRecord.is_deleted == False,
    ).first()
    if not record:
        return False

    record.is_deleted = True
    db.commit()

    # 删除关联的物理文件
    for path_str in [record.original_path, record.result_path]:
        p = Path(path_str)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    return True
