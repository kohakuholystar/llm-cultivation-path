"""Execute the trusted pytest file for one curriculum step."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.models.course import Step, Task
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse
from app.services.curriculum_loader import CurriculumCache
from app.services.sandbox_runner import get_runner


def get_step_for_validation(task_id: str, step_id: str) -> tuple[Task, Step, Path]:
    """Resolve all trusted data from the curriculum cache, never from a request path."""
    task = CurriculumCache.get_task(task_id)
    step = CurriculumCache.get_step(step_id)
    if task is None or step is None or step.task_id != task.id:
        raise HTTPException(404, "任务或步骤不存在")

    test_path = settings.data_path / "chapters" / task.chapter_id / task.id / f"{step.id}.test.py"
    if not test_path.is_file():
        raise HTTPException(409, "该步骤尚未迁移到行为测试，暂时使用页面内验证规则")
    return task, step, test_path


async def validate_step_code(task_id: str, step_id: str, code: str, env: dict[str, str] | None) -> SandboxRunResponse:
    task, step, test_path = get_step_for_validation(task_id, step_id)
    test_code = test_path.read_text(encoding="utf-8")
    needs_network = step.needs_network if step.needs_network is not None else task.needs_network
    timeout = step.sandbox_timeout or (30 if needs_network else 15)
    request = SandboxRunRequest(
        code=code,
        needs_network=needs_network,
        timeout=timeout,
        env=env if needs_network else None,
        sandbox_profile=step.sandbox_profile,
    )
    return await get_runner().run_pytest(request, test_code)
