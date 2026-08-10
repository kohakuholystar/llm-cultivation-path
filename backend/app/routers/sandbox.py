"""代码执行沙箱 API。"""
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse, SandboxStatus
from app.services.access_guard import check_access, check_rate_limit, log_run
from app.services.sandbox_runner import get_runner

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.post("/run")
async def run_code(req: SandboxRunRequest, request: Request) -> SandboxRunResponse:
    """执行学习者 Python 代码(Docker 沙箱, stdin 传代码)。

    公网部署防护: 访问口令(403) → IP 限流(429) → 资源隔离(runner 内)。
    """
    check_access(request)
    check_rate_limit(request)
    if not settings.sandbox_enabled:
        raise HTTPException(503, "沙箱已被配置禁用 (sandbox_enabled=False)")
    runner = get_runner()
    if not runner.is_available():
        raise HTTPException(503, "沙箱镜像未就绪, 请先运行 pnpm build:sandbox")
    resp = await runner.run(req)
    log_run(request, req, resp)
    return resp


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
