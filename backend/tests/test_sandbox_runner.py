"""沙箱联网配置与文件系统契约测试。"""

from __future__ import annotations

import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.course import Step
from app.models.sandbox import SandboxRunRequest
from app.services.sandbox_runner import SandboxConfigurationError, SandboxRunner


def test_network_run_requires_user_deepseek_key():
    runner = SandboxRunner()
    request = SandboxRunRequest(code="print('hello')", needs_network=True)

    with pytest.raises(SandboxConfigurationError, match="自己的 DeepSeek API Key"):
        runner._run_container(request)


def test_network_run_rejects_non_deepseek_endpoint():
    runner = SandboxRunner()
    request = SandboxRunRequest(
        code="print('hello')",
        needs_network=True,
        env={
            "OPENAI_API_KEY": "sk-user-key",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "MODEL_NAME": "deepseek-v4-pro",
        },
    )

    with pytest.raises(SandboxConfigurationError, match="DeepSeek 官方接口"):
        runner._run_container(request)


def test_sandbox_uses_isolated_writable_workspace(monkeypatch: pytest.MonkeyPatch):
    seen: list[str] = []

    def fake_run(cmd, **_kwargs):
        seen.extend(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr("app.services.sandbox_runner.subprocess.run", fake_run)
    runner = SandboxRunner()
    result = runner._run_container(SandboxRunRequest(code="print('ok')"))

    assert result.exit_code == 0
    assert result.stdout == "ok\n"
    assert "--read-only" in seen
    assert "--workdir=/workspace" in seen
    assert "--tmpfs=/workspace:rw,size=32m,mode=1777" in seen


def test_network_run_passes_only_user_deepseek_configuration(monkeypatch: pytest.MonkeyPatch):
    seen: list[str] = []

    def fake_run(cmd, **_kwargs):
        seen.extend(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"ok\n", stderr=b"")

    monkeypatch.setattr("app.services.sandbox_runner.subprocess.run", fake_run)
    runner = SandboxRunner()
    runner._run_container(
        SandboxRunRequest(
            code="print('ok')",
            needs_network=True,
            env={
                "OPENAI_API_KEY": "sk-user-key",
                "OPENAI_BASE_URL": "https://api.deepseek.com/v1",
                "MODEL_NAME": "deepseek-v4-pro",
                "UNRELATED_VALUE": "must-not-reach-container",
            },
        )
    )

    assert "OPENAI_API_KEY=sk-user-key" in seen
    assert "OPENAI_BASE_URL=https://api.deepseek.com" in seen
    assert "MODEL_NAME=deepseek-v4-pro" in seen
    assert not any("UNRELATED_VALUE" in item for item in seen)


def test_sandbox_api_returns_clear_error_for_missing_network_key(monkeypatch: pytest.MonkeyPatch):
    class RejectingRunner:
        def is_available(self, _profile: str = "core") -> bool:
            return True

        async def run(self, _request):
            raise SandboxConfigurationError("联网课程必须在 AI 配置中输入你自己的 DeepSeek API Key")

    monkeypatch.setattr("app.routers.sandbox.get_runner", lambda: RejectingRunner())
    response = TestClient(app).post(
        "/api/sandbox/run",
        json={"code": "print('hello')", "language": "python", "needsNetwork": True},
    )

    assert response.status_code == 400
    assert "自己的 DeepSeek API Key" in response.json()["detail"]


def test_step_validation_endpoint_uses_only_server_owned_test_files():
    with TestClient(app) as client:
        response = client.post(
            "/api/task/t01-deepseek-connect/step/t01-s1/validate",
            json={"code": "print('student code')"},
        )

    # The first test files have not been migrated yet, so the endpoint must not
    # accept arbitrary client-supplied test code or silently claim a pass.
    assert response.status_code == 409
    assert "行为测试" in response.json()["detail"]


def test_pytest_validation_uses_isolated_workspace(monkeypatch: pytest.MonkeyPatch):
    seen: list[str] = []

    def fake_run(cmd, **_kwargs):
        seen.extend(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"1 passed\n", stderr=b"")

    monkeypatch.setattr("app.services.sandbox_runner.subprocess.run", fake_run)
    result = SandboxRunner()._run_pytest_container(
        SandboxRunRequest(code="def add(a, b): return a + b"),
        "from student_submission import add\ndef test_add(): assert add(1, 2) == 3\n",
    )

    assert result.exit_code == 0
    assert "LEARNER_CODE_B64=" in "\n".join(seen)
    assert "STEP_TEST_B64=" in "\n".join(seen)
    assert "--workdir=/workspace" in seen
    assert "--tmpfs=/workspace:rw,size=32m,mode=1777" in seen

def test_step_supports_step_level_execution_metadata():
    step = Step.model_validate(
        {
            "id": "t99-s1",
            "taskId": "t99",
            "order": 1,
            "title": "step metadata",
            "instruction": "test",
            "starterCode": "# TODO\npass\n",
            "solutionCode": "print('ok')\n",
            "needsNetwork": True,
            "sandboxTimeout": 120,
            "sandboxProfile": "ml",
        }
    )

    assert step.needs_network is True
    assert step.sandbox_timeout == 120
    assert step.sandbox_profile == "ml"


def test_sandbox_request_allows_documented_extended_step_timeout():
    request = SandboxRunRequest(code="print('ok')", timeout=120)

    assert request.timeout == 120
