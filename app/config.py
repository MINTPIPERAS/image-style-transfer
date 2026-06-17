"""
应用配置，支持 .env 环境变量覆盖。
"""
import os
from pathlib import Path
from datetime import timedelta

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库（SQLite，文件存储在项目根目录）
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data.db")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(hours=2)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

# 文件存储根目录
STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))

# 图片上传限制
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# 风格迁移迭代次数
DEFAULT_ITERATIONS = int(os.getenv("DEFAULT_ITERATIONS", "10"))

# CORS 允许的前端地址
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# 预设风格（名称 → 文件名，文件位于 images/ 目录）
PRESET_STYLES = {
    "van_gogh":     {"name": "梵高",       "file": "style1.png"},
    "afremov":      {"name": "阿夫列莫夫", "file": "style2.png"},
    "picasso":      {"name": "毕加索",     "file": "style3.png"},
    "monet":        {"name": "莫奈",       "file": "style4.jpg"},
}
