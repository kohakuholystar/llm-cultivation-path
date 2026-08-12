"""Docker 沙箱执行器(subprocess 调 docker run, stdin 传代码, 避开路径映射)。

安全隔离:
- network=none(除非 needs_network)
- read-only 根文件系统 + 临时可写 /workspace
- cap_drop=ALL, no-new-privileges
- 非 root 用户, 内存 256m, CPU 0.5 核, 进程数 64
- 超时 kill
"""
from __future__ import annotations

import asyncio
import base64
import subprocess
import time
from urllib.parse import urlparse

from app.config import settings
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class SandboxConfigurationError(ValueError):
    """学习者的联网沙箱配置不满足课程要求。"""


def _normalize_deepseek_base_url(value: str) -> str:
    """只接受 DeepSeek 官方 API 端点，避免联网容器被导向任意地址。"""
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or parsed.netloc != "api.deepseek.com" or parsed.path not in ("", "/v1"):
        raise SandboxConfigurationError("联网课程只能使用 DeepSeek 官方接口 https://api.deepseek.com")
    return DEEPSEEK_BASE_URL


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
        if not self.is_available(req.sandbox_profile):
            image = settings.sandbox_ml_image if req.sandbox_profile == "ml" else self._image
            raise SandboxConfigurationError(f"{req.sandbox_profile} 教学沙箱镜像未就绪：{image}")
        async with self._sem:
            return await asyncio.to_thread(self._run_container, req)

    async def run_pytest(self, req: SandboxRunRequest, test_code: str) -> SandboxRunResponse:
        """Run trusted pytest against student code in an isolated per-run workspace."""
        if not self.is_available(req.sandbox_profile):
            image = settings.sandbox_ml_image if req.sandbox_profile == "ml" else self._image
            raise SandboxConfigurationError(f"{req.sandbox_profile} 教学沙箱镜像未就绪：{image}")
        async with self._sem:
            return await asyncio.to_thread(self._run_pytest_container, req, test_code)

    def _run_container(self, req: SandboxRunRequest) -> SandboxRunResponse:
        start = time.time()
        env = dict(req.env or {})
        if req.needs_network:
            api_key = env.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise SandboxConfigurationError("联网课程必须在 AI 配置中输入你自己的 DeepSeek API Key")
            model = env.get("MODEL_NAME", "").strip() or settings.generator_model
            if not model.startswith("deepseek-"):
                raise SandboxConfigurationError("联网课程的模型名必须是 DeepSeek 模型")
            env = {
                "OPENAI_API_KEY": api_key,
                "OPENAI_BASE_URL": _normalize_deepseek_base_url(
                    env.get("OPENAI_BASE_URL", DEEPSEEK_BASE_URL)
                ),
                "MODEL_NAME": model,
            }
        image = settings.sandbox_ml_image if req.sandbox_profile == "ml" else self._image
        cmd = [
            "docker", "run", "--rm", "-i",
            "--network=" + ("none" if not req.needs_network else "default"),
            "--memory=256m",
            "--cpus=0.5",
            "--read-only",
            "--tmpfs=/tmp:rw,size=32m",
            "--tmpfs=/workspace:rw,size=32m,mode=1777",
            "--workdir=/workspace",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=runner",
            "--pids-limit=64",
            # Some SDKs (notably CrewAI) consult HOME/XDG rather than cwd.
            # Keep their runtime state inside writable tmpfs, never the image layer.
            "-e", "HOME=/workspace",
            "-e", "XDG_CACHE_HOME=/tmp",
            "-e", "XDG_CONFIG_HOME=/tmp",
        ]
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])
        cmd.extend([
            image,
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

    def _run_pytest_container(self, req: SandboxRunRequest, test_code: str) -> SandboxRunResponse:
        """Materialize source and trusted tests inside /workspace, then invoke pytest.

        The test source is read only from the server's curriculum directory. Base64 prevents
        shell interpolation and keeps student code from becoming a command argument.
        """
        start = time.time()
        env = dict(req.env or {})
        if req.needs_network:
            api_key = env.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise SandboxConfigurationError("联网课程必须在 AI 配置中输入你自己的 DeepSeek API Key")
            model = env.get("MODEL_NAME", "").strip() or settings.generator_model
            if not model.startswith("deepseek-"):
                raise SandboxConfigurationError("联网课程的模型名必须是 DeepSeek 模型")
            env = {
                "OPENAI_API_KEY": api_key,
                "OPENAI_BASE_URL": _normalize_deepseek_base_url(env.get("OPENAI_BASE_URL", DEEPSEEK_BASE_URL)),
                "MODEL_NAME": model,
            }
        env["LEARNER_CODE_B64"] = base64.b64encode(req.code.encode("utf-8")).decode("ascii")
        env["STEP_TEST_B64"] = base64.b64encode(test_code.encode("utf-8")).decode("ascii")
        cmd = [
            "docker", "run", "--rm", "-i", "--network=" + ("none" if not req.needs_network else "default"),
            "--memory=256m", "--cpus=0.5", "--read-only", "--tmpfs=/tmp:rw,size=32m",
            "--tmpfs=/workspace:rw,size=32m,mode=1777", "--workdir=/workspace", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--user=runner", "--pids-limit=64",
            "-e", "HOME=/workspace", "-e", "XDG_CACHE_HOME=/tmp", "-e", "XDG_CONFIG_HOME=/tmp",
        ]
        for key, value in env.items():
            cmd.extend(["-e", f"{key}={value}"])
        setup = (
            "import base64, pathlib, pytest; "
            "pathlib.Path('student_submission.py').write_bytes(base64.b64decode(__import__('os').environ['LEARNER_CODE_B64'])); "
            "pathlib.Path('step_test.py').write_bytes(base64.b64decode(__import__('os').environ['STEP_TEST_B64'])); "
            "raise SystemExit(pytest.main(['-q', 'step_test.py']))"
        )
        image = settings.sandbox_ml_image if req.sandbox_profile == "ml" else self._image
        cmd.extend([image, "python", "-c", setup])
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=req.timeout)
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(stdout=proc.stdout.decode("utf-8", errors="replace"), stderr=proc.stderr.decode("utf-8", errors="replace"), exit_code=proc.returncode, duration_ms=duration_ms, timed_out=False)
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(stdout="", stderr=f"验证超时(>{req.timeout}秒, 已终止)", exit_code=-1, duration_ms=duration_ms, timed_out=True)
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            return SandboxRunResponse(stdout="", stderr=str(exc), exit_code=-1, duration_ms=duration_ms, timed_out=False, error=str(exc))

    def is_available(self, profile: str = "core") -> bool:
        """检查沙箱镜像是否就绪。"""
        image = settings.sandbox_ml_image if profile == "ml" else self._image
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image],
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
