"""FastAPI 应用入口。

M2: 挂载课程 router + 沙箱 router, lifespan 加载课程缓存, health 返回真实沙箱状态。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import curriculum, sandbox
from app.services.curriculum_loader import CurriculumCache
from app.services.sandbox_runner import get_runner

# 云端邀请码路由(公开库中被 sync 排除,不存在时跳过挂载,默认休眠)
try:
    from app.routers import access
except ImportError:
    access = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载课程数据到内存。"""
    try:
        CurriculumCache.load(settings.data_path)
        course = CurriculumCache.get_course()
        if course:
            print(
                f"[启动] 课程数据已加载: {len(course.chapters)} 章, "
                f"{sum(len(c.tasks) for c in course.chapters)} 任务"
            )
    except Exception as e:
        print(f"[启动] 警告: 课程数据加载失败: {e}")
    yield


app = FastAPI(
    title="LLM Agent 工程师修炼之路",
    description="打怪升级式 LLM 技术栈学习平台后端",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(curriculum.router)
if access is not None:  # 云端邀请码路由(公开库无此模块, 跳过)
    app.include_router(access.router)
app.include_router(sandbox.router)


@app.get("/")
async def root() -> dict:
    """根端点,验证服务启动。"""
    return {"msg": "hello", "name": "LLM Agent 工程师修炼之路"}


@app.get("/api/health")
async def health() -> dict:
    """健康检查,含沙箱镜像就绪状态。"""
    runner = get_runner()
    return {
        "status": "ok",
        "version": "1.0.0",
        "sandboxReady": runner.is_available(),
    }
