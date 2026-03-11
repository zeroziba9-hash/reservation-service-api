from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def signup_and_token(email: str, name: str, password: str):
    s = client.post("/auth/signup", json={"email": email, "name": name, "password": password})
    assert s.status_code in (200, 409)
    login = client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def dt(hour: int):
    return datetime(2026, 3, 10, hour, 0, 0, tzinfo=timezone.utc).isoformat()


def test_admin_can_create_resource_and_overlap_reservation_blocked():
    admin_headers = signup_and_token("admin@test.com", "admin", "pass1234")

    r = client.post("/resources", json={"name": "room-a"}, headers=admin_headers)
    assert r.status_code == 200
    resource_id = r.json()["id"]

    user_headers = signup_and_token("alice@test.com", "alice", "pass1234")

    ok = client.post(
        "/reservations",
        json={
            "resource_id": resource_id,
            "start_at": dt(10),
            "end_at": dt(12),
        },
        headers=user_headers,
    )
    assert ok.status_code == 200

    overlap = client.post(
        "/reservations",
        json={
            "resource_id": resource_id,
            "start_at": datetime(2026, 3, 10, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_at": datetime(2026, 3, 10, 13, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=user_headers,
    )
    assert overlap.status_code == 409
    assert overlap.json()["code"] == "HTTP_ERROR"


def test_owner_can_cancel_reservation_idempotent():
    admin_headers = signup_and_token("admin2@test.com", "admin2", "pass1234")
    r = client.post("/resources", json={"name": "room-b"}, headers=admin_headers)
    assert r.status_code == 200

    user_headers = signup_and_token("bob@test.com", "bob", "pass1234")

    created = client.post(
        "/reservations",
        json={
            "resource_id": r.json()["id"],
            "start_at": dt(13),
            "end_at": dt(14),
        },
        headers=user_headers,
    )
    assert created.status_code == 200

    reservation_id = created.json()["id"]
    canceled = client.post(f"/reservations/{reservation_id}/cancel", headers=user_headers)
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "CANCELED"

    canceled_again = client.post(f"/reservations/{reservation_id}/cancel", headers=user_headers)
    assert canceled_again.status_code == 200
    assert canceled_again.json()["status"] == "CANCELED"


def test_list_reservations_supports_pagination_status_and_scope():
    admin_headers = signup_and_token("admin3@test.com", "admin3", "pass1234")
    r = client.post("/resources", json={"name": "room-c"}, headers=admin_headers)
    assert r.status_code == 200

    user_headers = signup_and_token("charlie@test.com", "charlie", "pass1234")
    other_headers = signup_and_token("dave@test.com", "dave", "pass1234")

    base = datetime(2026, 3, 11, 9, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        created = client.post(
            "/reservations",
            json={
                "resource_id": r.json()["id"],
                "start_at": (base + timedelta(hours=i * 2)).isoformat(),
                "end_at": (base + timedelta(hours=i * 2 + 1)).isoformat(),
            },
            headers=user_headers,
        )
        assert created.status_code == 200

    other_created = client.post(
        "/reservations",
        json={
            "resource_id": r.json()["id"],
            "start_at": datetime(2026, 3, 12, 1, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_at": datetime(2026, 3, 12, 2, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=other_headers,
    )
    assert other_created.status_code == 200

    page = client.get("/reservations?limit=2&offset=1&status=BOOKED", headers=user_headers)
    assert page.status_code == 200
    assert len(page.json()) == 2

    bad_status = client.get("/reservations?status=PENDING", headers=user_headers)
    assert bad_status.status_code == 422
    assert bad_status.json()["code"] == "VALIDATION_ERROR"

    scoped = client.get("/reservations", headers=user_headers)
    assert scoped.status_code == 200
    assert len(scoped.json()) == 3

    admin_all = client.get("/reservations", headers=admin_headers)
    assert admin_all.status_code == 200
    assert len(admin_all.json()) == 4


def test_timezone_required_and_resource_crud():
    admin_headers = signup_and_token("admin4@test.com", "admin4", "pass1234")

    created = client.post("/resources", json={"name": "room-d"}, headers=admin_headers)
    assert created.status_code == 200
    resource_id = created.json()["id"]

    listed = client.get("/resources", headers=admin_headers)
    assert listed.status_code == 200
    assert any(x["name"] == "room-d" for x in listed.json())

    patched = client.patch(
        f"/resources/{resource_id}", json={"name": "room-d-1"}, headers=admin_headers
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "room-d-1"

    user_headers = signup_and_token("eve@test.com", "eve", "pass1234")
    naive_reservation = client.post(
        "/reservations",
        json={
            "resource_id": resource_id,
            "start_at": "2026-03-10T10:00:00",
            "end_at": "2026-03-10T11:00:00",
        },
        headers=user_headers,
    )
    assert naive_reservation.status_code == 400

    deleted = client.delete(f"/resources/{resource_id}", headers=admin_headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_delete_resource_allows_only_when_no_active_reservations():
    admin_headers = signup_and_token("admin10@test.com", "admin10", "pass1234")
    resource = client.post("/resources", json={"name": "room-j"}, headers=admin_headers)
    assert resource.status_code == 200
    resource_id = resource.json()["id"]

    user_headers = signup_and_token("ian@test.com", "ian", "pass1234")

    past_reservation = client.post(
        "/reservations",
        json={
            "resource_id": resource_id,
            "start_at": datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_at": datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=user_headers,
    )
    assert past_reservation.status_code == 200

    delete_with_only_past = client.delete(f"/resources/{resource_id}", headers=admin_headers)
    assert delete_with_only_past.status_code == 200

    resource2 = client.post("/resources", json={"name": "room-k"}, headers=admin_headers)
    assert resource2.status_code == 200
    resource2_id = resource2.json()["id"]

    future_reservation = client.post(
        "/reservations",
        json={
            "resource_id": resource2_id,
            "start_at": datetime(2099, 1, 1, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_at": datetime(2099, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=user_headers,
    )
    assert future_reservation.status_code == 200

    delete_with_active = client.delete(f"/resources/{resource2_id}", headers=admin_headers)
    assert delete_with_active.status_code == 409


def test_list_reservations_invalid_time_range_returns_400():
    admin_headers = signup_and_token("admin11@test.com", "admin11", "pass1234")
    resource = client.post("/resources", json={"name": "room-l"}, headers=admin_headers)
    assert resource.status_code == 200

    invalid_range = client.get(
        "/reservations?from_at=2026-03-12T12:00:00Z&to_at=2026-03-11T12:00:00Z",
        headers=admin_headers,
    )
    assert invalid_range.status_code == 400


def test_reservation_update():
    admin_headers = signup_and_token("admin5@test.com", "admin5", "pass1234")
    r = client.post("/resources", json={"name": "room-e"}, headers=admin_headers)
    assert r.status_code == 200

    user_headers = signup_and_token("frank@test.com", "frank", "pass1234")
    created = client.post(
        "/reservations",
        json={
            "resource_id": r.json()["id"],
            "start_at": dt(15),
            "end_at": dt(16),
        },
        headers=user_headers,
    )
    assert created.status_code == 200

    reservation_id = created.json()["id"]
    updated = client.patch(
        f"/reservations/{reservation_id}",
        json={
            "start_at": dt(16),
            "end_at": dt(17),
        },
        headers=user_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["start_at"].startswith("2026-03-10T16:00:00")


def test_create_reservation_with_idempotency_key_returns_same_result():
    admin_headers = signup_and_token("admin6@test.com", "admin6", "pass1234")
    resource = client.post("/resources", json={"name": "room-f"}, headers=admin_headers)
    assert resource.status_code == 200

    user_headers = signup_and_token("grace@test.com", "grace", "pass1234")
    idempotent_headers = {**user_headers, "idempotency-key": "idem-key-001"}

    payload = {
        "resource_id": resource.json()["id"],
        "start_at": dt(18),
        "end_at": dt(19),
    }
    first = client.post("/reservations", json=payload, headers=idempotent_headers)
    assert first.status_code == 200

    second = client.post("/reservations", json=payload, headers=idempotent_headers)
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    mismatch = client.post(
        "/reservations", json={**payload, "end_at": dt(20)}, headers=idempotent_headers
    )
    assert mismatch.status_code == 409


def test_idempotency_key_too_long_returns_400():
    admin_headers = signup_and_token("admin7@test.com", "admin7", "pass1234")
    resource = client.post("/resources", json={"name": "room-g"}, headers=admin_headers)
    assert resource.status_code == 200

    user_headers = signup_and_token("hannah@test.com", "hannah", "pass1234")
    too_long = "k" * 129
    headers = {**user_headers, "idempotency-key": too_long}

    res = client.post(
        "/reservations",
        json={
            "resource_id": resource.json()["id"],
            "start_at": dt(20),
            "end_at": dt(21),
        },
        headers=headers,
    )
    assert res.status_code == 400


def test_resources_and_reservations_support_success_envelope():
    admin_headers = signup_and_token("admin9@test.com", "admin9", "pass1234")
    env_headers = {**admin_headers, "X-Response-Envelope": "true"}

    created_resource = client.post("/resources", json={"name": "room-i"}, headers=env_headers)
    assert created_resource.status_code == 200
    created_body = created_resource.json()
    assert created_body["success"] is True
    assert created_body["data"]["name"] == "room-i"
    assert created_body["request_id"] == created_resource.headers.get("X-Request-ID")

    list_resources = client.get("/resources", headers=env_headers)
    assert list_resources.status_code == 200
    list_body = list_resources.json()
    assert list_body["success"] is True
    assert isinstance(list_body["data"], list)

    created_reservation = client.post(
        "/reservations",
        json={
            "resource_id": created_body["data"]["id"],
            "start_at": dt(22),
            "end_at": datetime(2026, 3, 10, 23, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=env_headers,
    )
    assert created_reservation.status_code == 200
    reservation_body = created_reservation.json()
    assert reservation_body["success"] is True
    assert reservation_body["data"]["status"] == "BOOKED"
