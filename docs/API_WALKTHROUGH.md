# API Walkthrough (Swagger Demo)

브라우저에서 `/docs`로 직접 시연할 때 쓰는 순서입니다.  
(스크린샷/예시 응답 파일은 정리 이슈로 현재 비워둔 상태)

## 0) 실행
- `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Swagger: `http://127.0.0.1:8000/docs`

---

## 1) 기본 플로우
1. `POST /auth/signup`
2. `POST /auth/login` (Authorize)
3. `POST /resources`
4. `POST /reservations`
5. `POST /reservations` (겹치는 시간으로 409 확인)
6. `GET /reservations`
7. `POST /reservations/{reservation_id}/cancel`

---

## 2) 확장 기능 플로우
1. `GET /resources`
2. `PATCH /resources/{resource_id}`
3. `DELETE /resources/{resource_id}`
4. `PATCH /reservations/{reservation_id}`
5. `POST /reservations/{reservation_id}/cancel` (2회 호출 멱등성)
6. `GET /reservations` (USER=본인, ADMIN=전체)
