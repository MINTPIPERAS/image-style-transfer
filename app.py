"""
图像风格迁移 Web 后端 (FastAPI)。

架构：
- POST /api/transfer     → 保存上传图片，启动独立子进程执行迁移，返回 task_id
- GET  /api/transfer/stream/{task_id} → SSE 流式推送子进程的实时进度
- GET  /api/output/{filename}        → 提供结果图片下载

子进程隔离方案：
  使用 asyncio.create_subprocess_exec 启动 run_transfer.py 独立进程。
  子进程将进度/结果通过 stdout 以 JSON 行输出，父进程异步读取并转为 SSE 事件。
  每次调用都是全新的 Python 进程 → TF 图天然隔离，无 Variable 命名冲突。
"""
import asyncio
import json
import shutil
import uuid
import threading
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("images")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ---- 任务注册表 ----
# tasks[task_id] = {"queue": asyncio.Queue, "status": str}
tasks: dict[str, dict] = {}
tasks_lock = threading.Lock()


def _cleanup_task(task_id: str):
    with tasks_lock:
        if task_id in tasks:
            del tasks[task_id]


@app.post("/api/transfer")
async def transfer_style_api(
    content_image: UploadFile = File(...),
    style_image: UploadFile = File(...),
):
    """创建风格迁移任务，启动独立子进程处理，立即返回 task_id."""
    # 1. 保存上传文件到 images/ 目录
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

    # 2. 启动独立子进程执行风格迁移
    #    stdout=PIPE 用于读取进度 JSON 行
    process = await asyncio.create_subprocess_exec(
        "python",
        "run_transfer.py",
        str(content_path),
        str(style_path),
        str(OUTPUT_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # 3. 注册任务
    task_id = uuid.uuid4().hex[:16]
    event_queue: asyncio.Queue = asyncio.Queue()

    with tasks_lock:
        tasks[task_id] = {
            "queue": event_queue,
            "status": "processing",
        }

    # 4. 后台异步任务：读取子进程 stdout，逐行推入 queue
    asyncio.create_task(_read_subprocess_stdout(task_id, process, event_queue))

    return JSONResponse({"task_id": task_id})


async def _read_subprocess_stdout(task_id: str, process: asyncio.subprocess.Process, event_queue: asyncio.Queue):
    """后台协程：逐行读取子进程 stdout，推入 asyncio 队列供 SSE 消费."""
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break  # EOF → 子进程已退出

            try:
                # TF/libclang 可能输出非 UTF-8 字节，用 errors='replace' 容错
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue
                event = json.loads(text)
                await event_queue.put(event)

                # 终端回显进度
                etype = event.get("event", "")
                data = event.get("data", {})
                if etype == "progress":
                    print(f"  [{data.get('iteration', '?')}/{data.get('total', '?')}] loss={data.get('loss', '?')}")
                elif etype == "complete":
                    print(f"  ✅ 风格迁移完成 → outputs/{data.get('filename', '?')}")
                elif etype == "failed":
                    print(f"  ❌ 风格迁移失败: {data.get('message', '未知错误')}")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        await event_queue.put({"event": "failed", "data": {"message": str(e)}})
    finally:
        # 确保子进程退出后再放一个标记
        await process.wait()
        # 如果子进程异常退出且未发送 complete/failed，补发一个
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

        _cleanup_task(task_id)


@app.get("/api/transfer/stream/{task_id}")
async def stream_progress(task_id: str):
    """SSE 端点：流式推送子进程的实时进度."""
    with tasks_lock:
        task_info = tasks.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    event_queue: asyncio.Queue = task_info["queue"]

    async def event_generator():
        while True:
            try:
                # asyncio 队列，timeout 1 秒
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                event_type = event.get("event", "message")
                data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"

                if event_type in ("complete", "failed"):
                    return  # 结束 SSE 流
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


@app.get("/api/output/{filename}")
async def get_output_image(filename: str):
    """获取风格迁移结果图片."""
    output_path = OUTPUT_DIR / filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(output_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
