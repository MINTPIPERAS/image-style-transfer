"""
图片风格转换路由 — 上传、提交转换、SSE 进度、历史记录、文件管理。
"""
import asyncio
import json
import sys
import uuid
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse

from app.config import DEFAULT_ITERATIONS
from app.middleware.auth import get_current_user, get_optional_user
from app.models.user import User
from app.models.conversion import ConversionRecord
from app.schemas.conversion import ConversionRecordOut, ConversionListResponse
from app.services.convert_service import (
    save_uploaded_file,
    create_conversion_record,
    get_user_records,
    soft_delete_record,
)

router = APIRouter(prefix="/api", tags=["风格转换"])

UPLOAD_DIR = Path("images")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 任务注册表（与原有 subprocess 方案兼容）
tasks: dict[str, dict] = {}
tasks_lock = threading.Lock()


def _cleanup_task(task_id: str):
    with tasks_lock:
        if task_id in tasks:
            del tasks[task_id]


# ============================================================
#  文件上传（需登录）
# ============================================================
@router.post("/convert/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传图片，保存到用户隔离目录，返回 file_id 和文件信息."""
    # 校验文件类型
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的格式：{ext}，仅支持 jpg/png/webp")

    # 校验大小（≤10MB）
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    file_path, stored_name = save_uploaded_file(
        current_user.id, file_bytes, file.filename
    )
    file_id = uuid.uuid4().hex[:16]

    return JSONResponse({
        "file_id": file_id,
        "filename": file.filename,
        "stored_name": stored_name,
        "path": str(file_path),
        "size": len(file_bytes),
    })


# ============================================================
#  提交转换任务（需登录）
#  支持两种模式：
#    1. 上传两张新图片（content_image + style_image）
#    2. 使用历史文件路径 + 参考风格图片
# ============================================================
@router.post("/convert/submit")
async def submit_transfer(
    content_image: UploadFile = File(...),
    style_image: UploadFile = File(...),
    style_type: str = Form(default="custom"),
    current_user: User = Depends(get_current_user),
):
    """提交风格迁移任务，返回 task_id 供 SSE 监听进度."""
    # 保存上传文件
    content_bytes = await content_image.read()
    style_bytes = await style_image.read()

    prefix = uuid.uuid4().hex[:8]
    content_filename = f"{prefix}_{content_image.filename}"
    style_filename = f"{prefix}_{style_image.filename}"

    content_path = UPLOAD_DIR / content_filename
    style_path = UPLOAD_DIR / style_filename

    with open(content_path, "wb") as f:
        f.write(content_bytes)
    with open(style_path, "wb") as f:
        f.write(style_bytes)

    original_size = len(content_bytes)

    # 启动子进程
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "run_transfer.py",
        str(content_path),
        str(style_path),
        str(OUTPUT_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    task_id = uuid.uuid4().hex[:16]
    event_queue: asyncio.Queue = asyncio.Queue()

    with tasks_lock:
        tasks[task_id] = {
            "queue": event_queue,
            "status": "processing",
            "user_id": current_user.id,
            "original_filename": content_image.filename,
            "original_path": str(content_path),
            "original_size": original_size,
            "style_type": style_type,
        }

    asyncio.create_task(
        _read_subprocess_stdout(task_id, process, event_queue, current_user.id)
    )

    return JSONResponse({"task_id": task_id})


async def _read_subprocess_stdout(
    task_id: str,
    process: asyncio.subprocess.Process,
    event_queue: asyncio.Queue,
    user_id: int,
):
    """后台协程：读取子进程 stdout，推送 SSE 事件。完成后自动创建数据库记录."""
    result_filename = None
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            try:
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue
                event = json.loads(text)
                await event_queue.put(event)

                etype = event.get("event", "")
                data = event.get("data", {})
                if etype == "complete":
                    result_filename = data.get("filename", "")
                    print(f"  [OK] Style transfer complete -> outputs/{result_filename}")
                elif etype == "progress":
                    print(f"  [{data.get('iteration', '?')}/{data.get('total', '?')}] "
                          f"loss={data.get('loss', '?')}")
                elif etype == "failed":
                    print(f"  [FAIL] Style transfer failed: {data.get('message', 'unknown error')}")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        await event_queue.put({"event": "failed", "data": {"message": str(e)}})
    finally:
        await process.wait()
        if process.returncode != 0:
            stderr_text = ""
            try:
                stderr_data = await process.stderr.read()
                stderr_text = stderr_data.decode("utf-8", errors="replace")[-500:]
            except Exception:
                pass
            await event_queue.put({
                "event": "failed",
                "data": {"message": f"子进程异常退出 (code={process.returncode}): {stderr_text}"},
            })

        # 完成后保存数据库记录（体验模式 user_id=0 时不保存）
        if result_filename and user_id > 0:
            task_info = tasks.get(task_id, {})
            result_path = OUTPUT_DIR / result_filename
            result_size = result_path.stat().st_size if result_path.exists() else 0

            # 需要 db session — 这里用独立导入避免循环依赖
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                create_conversion_record(
                    db=db,
                    user_id=user_id,
                    original_filename=task_info.get("original_filename", "unknown"),
                    original_path=task_info.get("original_path", ""),
                    result_filename=result_filename,
                    result_path=str(result_path),
                    style_type=task_info.get("style_type", "custom"),
                    original_size=task_info.get("original_size", 0),
                    result_size=result_size,
                    status="completed",
                )
            finally:
                db.close()

        _cleanup_task(task_id)


# ============================================================
#  SSE 进度流
# ============================================================
@router.get("/convert/task/{task_id}")
async def get_task_status(task_id: str):
    """SSE 端点：流式推送子进程的实时进度（登录用户）."""
    return await _sse_task_stream(task_id)


@router.get("/transfer/stream/{task_id}")
async def get_task_status_legacy(task_id: str):
    """SSE 端点：流式推送子进程的实时进度（体验模式）."""
    return await _sse_task_stream(task_id)


async def _sse_task_stream(task_id: str):
    """SSE 流的内部实现."""
    with tasks_lock:
        task_info = tasks.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    event_queue: asyncio.Queue = task_info["queue"]

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                event_type = event.get("event", "message")
                data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"
                if event_type in ("complete", "failed"):
                    return
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
#  文件提供（结果 + 原图）
# ============================================================
@router.get("/output/{filename}")
async def get_output_image(filename: str):
    """获取风格迁移结果图片（outputs/ 目录）."""
    output_path = OUTPUT_DIR / filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(output_path)


@router.get("/storage/user/{user_id}/{filename}")
async def get_user_file(user_id: int, filename: str):
    """获取用户隔离存储目录中的文件（原始上传图片）."""
    from app.services.convert_service import get_user_storage_dir
    file_path = get_user_storage_dir(user_id) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


# ============================================================
#  历史记录（需登录）
# ============================================================
@router.get("/convert/history", response_model=ConversionListResponse)
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的转换历史记录（分页）."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        records, total = get_user_records(db, current_user.id, page, page_size)
        items = []
        for r in records:
            items.append(ConversionRecordOut(
                id=r.id,
                original_filename=r.original_filename,
                style_type=r.style_type,
                original_size=r.original_size,
                result_size=r.result_size,
                status=r.status,
                created_at=r.created_at,
                result_url=f"/api/output/{r.result_filename}",
                original_url=f"/api/storage/user/{current_user.id}/{Path(r.original_path).name}",
            ))
        return ConversionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    finally:
        db.close()


@router.delete("/convert/record/{record_id}")
async def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
):
    """软删除一条转换记录及关联文件."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        success = soft_delete_record(db, record_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="记录不存在或无权操作")
        return JSONResponse({"message": "已删除"})
    finally:
        db.close()


# ============================================================
#  保留原接口兼容（不需要登录的体验模式）
# ============================================================
@router.post("/transfer")
async def transfer_style_api_legacy(
    content_image: UploadFile = File(...),
    style_image: UploadFile = File(...),
):
    """体验模式风格迁移（无需登录，不保存记录）."""
    prefix = uuid.uuid4().hex[:8]
    content_filename = f"{prefix}_{content_image.filename}"
    style_filename = f"{prefix}_{style_image.filename}"

    content_path = UPLOAD_DIR / content_filename
    style_path = UPLOAD_DIR / style_filename

    content_bytes = await content_image.read()
    style_bytes = await style_image.read()

    with open(content_path, "wb") as f:
        f.write(content_bytes)
    with open(style_path, "wb") as f:
        f.write(style_bytes)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "run_transfer.py",
        str(content_path),
        str(style_path),
        str(OUTPUT_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    task_id = uuid.uuid4().hex[:16]
    event_queue: asyncio.Queue = asyncio.Queue()

    with tasks_lock:
        tasks[task_id] = {
            "queue": event_queue,
            "status": "processing",
        }

    # user_id=0 表示体验模式，_read_subprocess_stdout 会跳过数据库记录
    asyncio.create_task(_read_subprocess_stdout(task_id, process, event_queue, user_id=0))
    return JSONResponse({"task_id": task_id})
