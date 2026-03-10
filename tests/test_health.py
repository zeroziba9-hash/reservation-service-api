from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert "X-Request-ID" in res.headers


def test_health_with_envelope():
    res = client.get("/health", headers={"X-Response-Envelope": "true"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["request_id"] == res.headers.get("X-Request-ID")


def test_ready():
    res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["db"] == "ok"


def test_request_id_propagates_to_error_response():
    res = client.post(
        "/auth/signup",
        json={"email": "not-an-email", "name": "x", "password": "123"},
    )
    assert res.status_code == 422
    body = res.json()
    assert body["request_id"] is not None
    assert res.headers.get("X-Request-ID") == body["request_id"]
