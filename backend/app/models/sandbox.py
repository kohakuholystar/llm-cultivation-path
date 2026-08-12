"""沙箱请求/响应模型(与 shared/types/sandbox.ts 对齐)。"""
from typing import Literal, Optional

from pydantic import Field

from app.models.course import CamelModel


class SandboxRunRequest(CamelModel):
    code: str = Field(..., max_length=50_000)
    language: str = "python"
    timeout: int = Field(10, ge=1, le=120)
    needs_network: bool = False
    stdin: Optional[str] = None
    env: Optional[dict[str, str]] = None
    sandbox_profile: Literal["core", "ml"] = "core"


class SandboxRunResponse(CamelModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    timed_out: bool
    error: Optional[str] = None


class StepValidationRequest(CamelModel):
    """权威步骤验证请求；步骤 ID、测试文件和沙箱策略均不由前端决定。"""

    code: str = Field(..., max_length=50_000)
    env: Optional[dict[str, str]] = None


class StepValidationResponse(CamelModel):
    step_id: str
    passed: bool
    output: SandboxRunResponse


class SandboxStatus(CamelModel):
    available: bool
    image: str
    concurrency: int
    max_concurrency: int
