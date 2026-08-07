"""沙箱请求/响应模型(与 shared/types/sandbox.ts 对齐)。"""
from typing import Optional

from pydantic import Field

from app.models.course import CamelModel


class SandboxRunRequest(CamelModel):
    code: str = Field(..., max_length=50_000)
    language: str = "python"
    timeout: int = Field(10, ge=1, le=30)
    needs_network: bool = False
    stdin: Optional[str] = None
    env: Optional[dict[str, str]] = None


class SandboxRunResponse(CamelModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    timed_out: bool
    error: Optional[str] = None


class SandboxStatus(CamelModel):
    available: bool
    image: str
    concurrency: int
    max_concurrency: int
