# API Walkthrough (Swagger Demo + Screenshots)

브라우저에서 `/docs`로 직접 시연할 때 쓰는 순서입니다.  
기존 캡처 이미지는 `docs/screenshots`에 정리했습니다.

## 0) 실행
- `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Swagger: `http://127.0.0.1:8000/docs`

---

## 1) Signup
- API: `POST /auth/signup`
- Screenshot: `docs/screenshots/01_signup.png`
- Example result: `docs/screenshots/01_signup.json`

## 2) Login (Authorize)
- API: `POST /auth/login`
- Screenshot: `docs/screenshots/02_login.png`
- Example result: `docs/screenshots/02_login.json`

## 3) Create Resource
- API: `POST /resources`
- Screenshot: `docs/screenshots/03_create_resource.png`
- Example result: `docs/screenshots/03_create_resource.json`

## 4) Create Reservation
- API: `POST /reservations`
- Screenshot: `docs/screenshots/04_create_reservation.png`
- Example result: `docs/screenshots/04_create_reservation.json`

## 5) Conflict Reservation (409)
- API: `POST /reservations` (겹치는 시간)
- Screenshot: `docs/screenshots/05_conflict_reservation.png`
- Example result: `docs/screenshots/05_conflict_reservation.json`

## 6) List Reservations
- API: `GET /reservations`
- Screenshot: `docs/screenshots/06_list_reservations.png`
- Example result: `docs/screenshots/06_list_reservations.json`

## 7) Cancel Reservation
- API: `POST /reservations/{reservation_id}/cancel`
- Screenshot: `docs/screenshots/07_cancel_reservation.png`
- Example result: `docs/screenshots/07_cancel_reservation.json`

---

## 8) New features demo (이번 라운드 추가)
아래는 이번에 추가한 기능들입니다. 스웨거에서 같은 방식으로 캡처 누적하면 됩니다.

- `GET /resources` (리소스 목록)
- `PATCH /resources/{resource_id}` (리소스명 수정)
- `DELETE /resources/{resource_id}` (리소스 삭제)
- `PATCH /reservations/{reservation_id}` (예약 시간 변경)
- `POST /reservations/{reservation_id}/cancel` 멱등성 (두 번 호출해도 200)
- `GET /reservations` 권한 스코프 (USER=본인, ADMIN=전체)

권장 캡처 파일명:
- `08_list_resources.png`
- `09_update_resource.png`
- `10_delete_resource.png`
- `11_update_reservation.png`
- `12_cancel_idempotent.png`
- `13_reservation_scope_user_vs_admin.png`
