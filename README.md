# reservation-service-api

실무 지향 **FastAPI 예약 서비스 템플릿**입니다.  
Production-minded reservation API template with auth, RBAC, safe booking flow, and predictable API behavior.

---

## ✅ Features

- Health/Readiness endpoint (`GET /health`, `GET /ready` with DB ping)
- JWT 인증 (`/auth/signup`, `/auth/login`)
- Role 기반 권한 제어 (최초 가입자 `ADMIN`)
- 리소스 CRUD (`ADMIN` 전용)
- 예약 생성/수정/취소 + 권한 분리 (`USER=본인`, `ADMIN=전체`)
- 예약 중복 방지
  - API 레벨 충돌 검사 (`409 Conflict`)
  - PostgreSQL 환경에서는 `EXCLUDE` 제약으로 DB 레벨 보호
- `Idempotency-Key` 기반 예약 생성 멱등 처리 (Redis)
- 예약 조회 필터 + 페이지네이션
  - `status`, `resource_id`, `from_at`, `to_at`, `limit`, `offset`
- 표준 에러 응답 포맷 (일관된 에러 바디)
- Audit Log 기록 (`signup`, `resource`, `reservation`)
- 구조화 로그(JSON) + Request ID (`X-Request-ID`) 추적
- 선택형 성공 응답 래퍼 (`X-Response-Envelope: true`)
- Alembic migration baseline
- Ruff + Black + Pytest + GitHub Actions CI

---

## 🧱 Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL (권장) / SQLite (로컬 빠른 시작)
- Redis
- Alembic
- Pytest
- GitHub Actions

---

## ⚙️ Environment Variables

`.env` 예시:

```env
APP_ENV=dev
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-this-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
IDEMPOTENCY_TTL_SECONDS=86400
IDEMPOTENCY_LOCK_SECONDS=30
```

---

## 🚀 Quick Start

### 1) Local (SQLite)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

### 2) Windows helper scripts

```powershell
./scripts/dev_start.ps1
```

### 3) PostgreSQL mode (Docker Compose + migration + run)

```powershell
./scripts/dev_start_pg.ps1
```

### 4) Quality Gate (format/lint/migration/test)

```powershell
./scripts/check.ps1
```

Swagger Docs:
- `http://127.0.0.1:8000/docs`

> 예약 시간 입력은 timezone 포함 ISO8601(UTC 권장) 사용

---

## 🧪 Tests

```bash
python -m pytest -q
```

Expected:
- `14 passed`

---

## 🔒 Reservation Safety Notes

### 1) Overlap protection
- 동일 리소스의 예약 시간 겹침은 `409` 반환
- PostgreSQL에서는 `EXCLUDE USING gist`로 DB 레벨에서도 방어

### 2) Resource deletion guard
- **활성 예약(`BOOKED` + `end_at > now`)이 있으면** 리소스 삭제 불가 (`409`)
- 과거 예약만 남아있으면 삭제 가능

### 3) Idempotency-Key behavior
- 헤더 없음: 일반 생성
- 같은 Key + 같은 payload: 같은 결과 재반환
- 같은 Key + 다른 payload: `409`
- 같은 Key 요청 처리 중 중복 요청: `409 (in progress)`

---

## 📡 Main Endpoints

- `GET /health`
- `GET /ready`
- `POST /auth/signup`
- `POST /auth/login`
- `POST /resources` (admin)
- `GET /resources` (auth)
- `PATCH /resources/{resource_id}` (admin)
- `DELETE /resources/{resource_id}` (admin)
- `POST /reservations` (auth, optional `Idempotency-Key`)
- `PATCH /reservations/{reservation_id}` (owner/admin)
- `GET /reservations` (auth)
- `POST /reservations/{reservation_id}/cancel` (owner/admin)

---

## 🧯 Standard Error Response

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

## 📁 Project Structure

- `app/api/routes.py` : API endpoints
- `app/core/security.py` : JWT/password hashing
- `app/core/errors.py` : global exception mapping
- `app/models.py` : User/Resource/Reservation/AuditLog
- `alembic/` : migration scripts
- `tests/` : test suite
