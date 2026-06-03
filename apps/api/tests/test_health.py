# apps/api/tests/test_health.py
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_body(client: TestClient):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["service"] == "academy-api"
