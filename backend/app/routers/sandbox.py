"""代码执行沙箱 API。"""
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse, SandboxStatus
from app.services.sandbox_runner import get_runner

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.post("/run")
async def run_code(req: SandboxRunRequest) -> SandboxRunResponse:
    """执行学习者 Python 代码(Docker 沙箱, stdin 传代码)。"""
    if not settings.sandbox_enabled:
        raise HTTPException(503, "沙箱已被配置禁用 (sandbox_enabled=False)")
    runner = get_runner()
    if not runner.is_available():
        raise HTTPException(503, "沙箱镜像未就绪, 请先运行 pnpm build:sandbox")
    return await runner.run(req)


@router.get("/status")
async def sandbox_status() -> SandboxStatus:
    """沙箱状态(镜像是否就绪, 当前并发)。"""
    runner = get_runner()
    available = runner.is_available()
    return SandboxStatus(
        available=available,
        image=runner._image,
        concurrency=runner.concurrency,
        max_concurrency=runner.max_concurrency,
    )
