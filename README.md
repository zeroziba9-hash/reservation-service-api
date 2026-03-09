# reservation-service-api

실무 지향 FastAPI 예약 서비스 템플릿입니다.  
Production-minded reservation API template with auth, RBAC, and safe booking flow.

---

## 1) 핵심 기능 (Included Features)
- Health check endpoint (`GET /health`)
- JWT 인증 (signup/login)
- Role 기반 권한 제어 (첫 가입자 ADMIN)
- 예약 중복 방지 (409 Conflict)
- 예약 취소 (owner/admin)
- 예약 조회 필터 (`status`, `resource_id`, `from_at`, `to_at`)
- Audit log 기록 (signup/resource create/reservation create/cancel)
- 표준 에러 응답 포맷 (standardized error body)
- Alembic migration baseline
- Pytest + GitHub Actions CI

---

## 2) 기술 스택 (Tech Stack)
- FastAPI
- SQLAlchemy
- PostgreSQL (default infra) / SQLite (local quick start)
- Redis
- Alembic
- Pytest
- GitHub Actions

---

## 3) 빠른 실행 (Quick Start)
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger Docs:
- `http://127.0.0.1:8000/docs`

---

## 4) 테스트 (Tests)
```bash
pytest -q
```

Expected result:
- `3 passed`

---

## 5) 마이그레이션 (Migration)
```bash
alembic upgrade head
```

---

## 6) 인프라 (Infra)
```bash
docker compose up -d
```

---

## 7) 주요 API (Main Endpoints)
- `GET /health`
- `POST /auth/signup`
- `POST /auth/login`
- `POST /resources` (admin only)
- `POST /reservations` (auth required)
- `GET /reservations` (auth required)
- `POST /reservations/{reservation_id}/cancel` (owner/admin)

---

## 8) 표준 에러 응답 (Standard Error Body)
```json
{
  "timestamp": "2026-03-09T14:00:00Z",
  "status": 409,
  "code": "HTTP_ERROR",
  "message": "time slot already booked",
  "detail": []
}
```

---

## 9) 프로젝트 구조 (Project Structure)
- `app/api/routes.py` : API 엔드포인트
- `app/core/security.py` : JWT, password hash
- `app/core/errors.py` : 전역 예외 응답 포맷
- `app/models.py` : User/Resource/Reservation/AuditLog
- `alembic/` : DB migration scripts
- `tests/` : API 테스트 코드
