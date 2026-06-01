"""
独立的风格迁移执行脚本（subprocess 隔离）。

通过 stdout 输出 JSON 行来报告进度和结果，父进程通过读取 stdout 获取实时进度。
这种设计：
1. 每次调用都是完全独立的 Python 进程，TF 图天然隔离
2. 不需要 mp.Queue / callback / 线程 —— 零序列化风险
3. 完全还原原始 transfer_style.py 的执行方式
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from transfer_style import process_image


def emit(event_type: str, data: dict):
    """向 stdout 输出一行 JSON，父进程通过管道读取."""
    line = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)
    print(line, flush=True)


def progress_callback(iteration: int, total: int, loss: float):
    emit("progress", {"iteration": iteration, "total": total, "loss": round(loss, 2)})


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python run_transfer.py <content_path> <style_path> <output_dir>", file=sys.stderr)
        sys.exit(2)

    content_path = sys.argv[1]
    style_path = sys.argv[2]
    output_dir = sys.argv[3]

    try:
        result_filename = process_image(
            content_path,
            style_path,
            output_dir,
            progress_callback=progress_callback,
        )
        emit("complete", {"filename": result_filename})
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        emit("failed", {"message": str(e)})
        sys.exit(1)
