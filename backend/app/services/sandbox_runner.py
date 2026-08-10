"""Docker 沙箱执行器(subprocess 调 docker run, stdin 传代码, 避开路径映射)。

安全隔离:
- network=none(除非 needs_network)
- read-only 根文件系统 + tmpfs /tmp
- cap_drop=ALL, no-new-privileges
- 非 root 用户, 内存 256m, CPU 0.5 核, 进程数 64
- 超时 kill
"""
from __future__ import annotations

import asyncio
import subprocess
import time

from app.config import settings
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse


class SandboxRunner:
    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(settings.sandbox_max_concurrency)
        self._image = settings.sandbox_image

    @property
    def max_concurrency(self) -> int:
        return settings.sandbox_max_concurrency

    @property
    def concurrency(self) -> int:
        """当前正在执行的沙箱数(信号量已占用槽位)。"""
        return settings.sandbox_max_concurrency - self._sem._value

    async def run(self, req: SandboxRunRequest) -> SandboxRunResponse:
        async with self._sem:
            return await asyncio.to_thread(self._run_container, req)

    def _run_container(self, req: SandboxRunRequest) -> SandboxRunResponse:
        start = time.time()
        cmd = [
            "docker", "run", "--rm", "-i",
            "--network=" + ("none" if not req.needs_network else "default"),
            "--memory=256m",
            "--cpus=0.5",
            "--read-only",
            "--tmpfs=/tmp:rw,size=10m",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=runner",
            "--pids-limit=64",
        ]
        # needs_network 时自动注入 LLM 配置(让学习者代码能调国内 AI)
        # 优先级: 前端传的 env(req.env) > 后端 .env(settings)。
        # setdefault 语义: 前端已传的 key 不覆盖, 未传的才用后端默认值 fallback。
        env = dict(req.env or {})
        if req.needs_network:
            env.setdefault("OPENAI_API_KEY", settings.openai_api_key)
            env.setdefault("OPENAI_BASE_URL", settings.openai_base_url)
            env.setdefault("MODEL_NAME", settings.generator_model)
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])
        cmd.extend([
            self._image,
            # 用 compile 指定文件名 'main.py':让 traceback 的行号与前端编辑器里的
            # main.py 对应,而不是指向无法定位的 <string>。
            "python", "-c", "import sys; exec(compile(sys.stdin.read(), 'main.py', 'exec'))",
        ])
        try:
            proc = subprocess.run(
                cmd,
                input=req.code.encode("utf-8"),
                capture_output=True,
                timeout=req.timeout,
            )
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(
                stdout=proc.stdout.decode("utf-8", errors="replace"),
                stderr=proc.stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode,
                duration_ms=duration_ms,
                timed_out=False,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(
                stdout="",
                stderr=f"执行超时(>{req.timeout}秒, 已终止)",
                exit_code=-1,
                duration_ms=duration_ms,
                timed_out=True,
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration_ms,
                timed_out=False,
                error=str(e),
            )

    def is_available(self) -> bool:
        """检查沙箱镜像是否就绪。"""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self._image],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False


_runner: SandboxRunner | None = None


def get_runner() -> SandboxRunner:
    global _runner
    if _runner is None:
        _runner = SandboxRunner()
    return _runner
