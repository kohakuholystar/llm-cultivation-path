"""健康检查与基础端点测试。"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_hello():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["msg"] == "hello"
    assert "name" in data


def test_health_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "sandboxReady" in data


def test_cors_header_present():
    """CORS 中间件应正确响应 OPTIONS 预检。"""
    resp = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3200",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3200"
