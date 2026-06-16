"""
FastAPI 应用入口 — 图片风格转换系统 v2.0。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL
from app.database import init_db
from app.routers import auth, users, convert


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库表."""
    init_db()
    print("[OK] Database tables initialized")
    yield


app = FastAPI(
    title="图片风格转换系统",
    description="基于 VGG16 的神经风格迁移 Web 应用，支持用户体系与历史记录",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(convert.router)


@app.get("/api/health")
async def health_check():
    """健康检查端点."""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
