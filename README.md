# reservation-service-api

실무 지향 FastAPI 예약 서비스 템플릿입니다.  
Production-minded reservation API template with auth, RBAC, and safe booking flow.

---

## 1) 핵심 기능 (Included Features)
- Health check endpoint (`GET /health`, DB ping 포함)
- JWT 인증 (signup/login)
- Role 기반 권한 제어 (첫 가입자 ADMIN)
- 리소스 CRUD (admin only)
- 예약 중복 방지 (409 Conflict)
- 예약 수정 / 취소 (owner/admin)
- 예약 조회 필터 + 페이지네이션 (`status`, `resource_id`, `from_at`, `to_at`, `limit`, `offset`)
- 예약 조회 권한 분리 (USER=본인, ADMIN=전체)
- 예약 취소 멱등 처리 (이미 취소된 건 재요청 시 200)
- Audit log 기록 (signup/resource/reservation)
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

## 3) 환경 변수 (.env)
`.env` 파일 예시:

```env
APP_ENV=dev
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-this-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 4) 빠른 실행 (Quick Start)
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Windows one-command start:
```powershell
./scripts/dev_start.ps1
```

Swagger Docs:
- `http://127.0.0.1:8000/docs`

> 예약 시간 입력은 timezone 포함 ISO8601(UTC 권장) 사용

---

## 5) 테스트 (Tests)
```bash
python -m pytest -q
```

Expected result:
- `6 passed`

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
- `POST /resources` (admin)
- `GET /resources` (auth)
- `PATCH /resources/{resource_id}` (admin)
- `DELETE /resources/{resource_id}` (admin)
- `POST /reservations` (auth)
- `PATCH /reservations/{reservation_id}` (owner/admin)
- `GET /reservations` (auth)
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
