from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_database
from config import settings
from routers import novels, characters, chapters, channels, ai, outlines, logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_database()
    print("数据库初始化完成")
    yield
    # 关闭时清理资源
    print("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI小说写作系统",
    description="基于AI的本地小说创作工具",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(novels.router)
app.include_router(characters.router)
app.include_router(chapters.router)
app.include_router(channels.router)
app.include_router(ai.router)
app.include_router(outlines.router)
app.include_router(logs.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI小说写作系统 API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
