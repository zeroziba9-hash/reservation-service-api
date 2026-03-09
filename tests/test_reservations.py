from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def signup_and_token(email: str, name: str, password: str):
    s = client.post('/auth/signup', json={"email": email, "name": name, "password": password})
    assert s.status_code in (200, 409)
    l = client.post('/auth/login', data={"username": email, "password": password})
    assert l.status_code == 200
    token = l.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_resource_and_overlap_reservation_blocked():
    admin_headers = signup_and_token("admin@test.com", "admin", "pass1234")

    r = client.post('/resources', json={'name': 'room-a'}, headers=admin_headers)
    assert r.status_code == 200
    resource_id = r.json()['id']

    user_headers = signup_and_token("alice@test.com", "alice", "pass1234")

    start = datetime(2026, 3, 10, 10, 0, 0)
    end = start + timedelta(hours=2)

    ok = client.post('/reservations', json={
        'resource_id': resource_id,
        'start_at': start.isoformat(),
        'end_at': end.isoformat(),
    }, headers=user_headers)
    assert ok.status_code == 200

    overlap = client.post('/reservations', json={
        'resource_id': resource_id,
        'start_at': (start + timedelta(minutes=30)).isoformat(),
        'end_at': (end + timedelta(minutes=30)).isoformat(),
    }, headers=user_headers)
    assert overlap.status_code == 409
    assert overlap.json()["code"] == "HTTP_ERROR"

    booked_only = client.get('/reservations?status=BOOKED', headers=user_headers)
    assert booked_only.status_code == 200
    assert len(booked_only.json()) == 1


def test_owner_can_cancel_reservation():
    admin_headers = signup_and_token("admin2@test.com", "admin2", "pass1234")
    r = client.post('/resources', json={'name': 'room-b'}, headers=admin_headers)
    assert r.status_code == 200

    user_headers = signup_and_token("bob@test.com", "bob", "pass1234")

    start = datetime(2026, 3, 10, 13, 0, 0)
    end = start + timedelta(hours=1)

    created = client.post('/reservations', json={
        'resource_id': r.json()['id'],
        'start_at': start.isoformat(),
        'end_at': end.isoformat(),
    }, headers=user_headers)
    assert created.status_code == 200

    reservation_id = created.json()['id']
    canceled = client.post(f"/reservations/{reservation_id}/cancel", headers=user_headers)
    assert canceled.status_code == 200
    assert canceled.json()['status'] == 'CANCELED'
