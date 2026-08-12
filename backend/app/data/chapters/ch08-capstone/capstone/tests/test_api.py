from fastapi.testclient import TestClient

from app.api import create_app


def test_health_check_is_an_explicit_contract() -> None:
    response = TestClient(create_app()).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
