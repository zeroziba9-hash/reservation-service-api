from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_overlap_reservation():
    u = client.post('/users', json={'name': 'alice', 'role': 'USER'}).json()
    r = client.post('/resources', json={'name': 'room-a'}).json()

    start = datetime(2026, 3, 10, 10, 0, 0)
    end = start + timedelta(hours=2)

    ok = client.post('/reservations', json={
        'user_id': u['id'],
        'resource_id': r['id'],
        'start_at': start.isoformat(),
        'end_at': end.isoformat(),
    })
    assert ok.status_code == 200

    overlap = client.post('/reservations', json={
        'user_id': u['id'],
        'resource_id': r['id'],
        'start_at': (start + timedelta(minutes=30)).isoformat(),
        'end_at': (end + timedelta(minutes=30)).isoformat(),
    })
    assert overlap.status_code == 409


def test_cancel_reservation():
    u = client.post('/users', json={'name': 'bob', 'role': 'USER'}).json()
    r = client.post('/resources', json={'name': 'room-b'}).json()

    start = datetime(2026, 3, 10, 13, 0, 0)
    end = start + timedelta(hours=1)

    created = client.post('/reservations', json={
        'user_id': u['id'],
        'resource_id': r['id'],
        'start_at': start.isoformat(),
        'end_at': end.isoformat(),
    }).json()

    canceled = client.post(f"/reservations/{created['id']}/cancel")
    assert canceled.status_code == 200
    assert canceled.json()['status'] == 'CANCELED'
