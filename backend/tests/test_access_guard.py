"""公网防护测试: 访问口令(403) + IP 限流(429)。

口令/限流都挡在沙箱可用性检查之前, 因此用 sandbox_enabled=False 制造
确定性的 503 作为"已通过防护"的信号, 无需 Docker 即可测试。
"""
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import access_guard

client = TestClient(app)

BODY = {"code": "print(1+1)"}


@pytest.fixture(autouse=True)
def _guard_state(monkeypatch):
    """每用例重置: 关闭沙箱(确定性的 503)、清空限流桶、恢复配置。"""
    monkeypatch.setattr(settings, "sandbox_enabled", False)
    access_guard._buckets.clear()
    yield


def test_open_when_no_codes(monkeypatch):
    """未配置口令 = 门槛关闭, 直连到沙箱检查(503 表示穿过了防护)。"""
    monkeypatch.setattr(settings, "access_codes", "")
    monkeypatch.setattr(settings, "sandbox_rate_limit", 0)
    resp = client.post("/api/sandbox/run", json=BODY)
    assert resp.status_code == 503


def test_forbidden_with_wrong_code(monkeypatch):
    monkeypatch.setattr(settings, "access_codes", "xianxia-2026, vip-888")
    monkeypatch.setattr(settings, "sandbox_rate_limit", 0)
    resp = client.post("/api/sandbox/run", json=BODY)
    assert resp.status_code == 403
    resp2 = client.post("/api/sandbox/run", json=BODY, headers={"X-Access-Code": "wrong"})
    assert resp2.status_code == 403


def test_pass_with_right_code(monkeypatch):
    monkeypatch.setattr(settings, "access_codes", "xianxia-2026, vip-888")
    monkeypatch.setattr(settings, "sandbox_rate_limit", 0)
    resp = client.post(
        "/api/sandbox/run", json=BODY, headers={"X-Access-Code": "vip-888"}
    )
    assert resp.status_code == 503  # 穿过口令, 被 sandbox_enabled=False 拦下


def test_rate_limit_kicks_in(monkeypatch):
    monkeypatch.setattr(settings, "access_codes", "")
    monkeypatch.setattr(settings, "sandbox_rate_limit", 3)
    codes = [
        client.post("/api/sandbox/run", json=BODY).status_code for _ in range(4)
    ]
    assert codes[:3] == [503, 503, 503]
    assert codes[3] == 429


def test_rate_limit_off_when_zero(monkeypatch):
    monkeypatch.setattr(settings, "access_codes", "")
    monkeypatch.setattr(settings, "sandbox_rate_limit", 0)
    codes = [
        client.post("/api/sandbox/run", json=BODY).status_code for _ in range(5)
    ]
    assert all(c == 503 for c in codes)
