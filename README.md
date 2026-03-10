# reservation-service-api

실무 지향 FastAPI 예약 서비스 템플릿입니다.  
Production-minded reservation API template with auth, RBAC, and safe booking flow.

---

## 1) 핵심 기능 (Included Features)
- Health/Readiness endpoint (`GET /health`, `GET /ready` with DB ping)
- JWT 인증 (signup/login)
- Role 기반 권한 제어 (첫 가입자 ADMIN)
- 리소스 CRUD (admin only)
- 예약 중복 방지 (409 Conflict, PostgreSQL은 EXCLUDE 제약으로 DB 레벨 보호)
- 예약 생성 Idempotency-Key 지원 (Redis 기반 중복 요청 방지)
- 예약 수정 / 취소 (owner/admin)
- 예약 조회 필터 + 페이지네이션 (`status`, `resource_id`, `from_at`, `to_at`, `limit`, `offset`)
- 예약 조회 권한 분리 (USER=본인, ADMIN=전체)
- 예약 취소 멱등 처리 (이미 취소된 건 재요청 시 200)
- Audit log 기록 (signup/resource/reservation)
- 표준 에러 응답 포맷 (standardized error body)
- Alembic migration baseline
- 구조화 로그(JSON) + Request ID (`X-Request-ID`) 추적
- 성공 응답 래퍼(2차): `X-Response-Envelope: true` (health/ready/auth/resources/reservations)
- Ruff + Black + Pytest + GitHub Actions CI

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
IDEMPOTENCY_TTL_SECONDS=86400
IDEMPOTENCY_LOCK_SECONDS=30
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

Windows PostgreSQL start (docker compose + migration + run):
```powershell
./scripts/dev_start_pg.ps1
```

Windows quality gate check:
```powershell
./scripts/check.ps1
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
- `12 passed`

---

## 6) PostgreSQL 동시성 보호 (DB Constraint)
- Alembic `0002_pg_exclusion_constraint`는 PostgreSQL에서만 적용됩니다.
- `reservations` 테이블에 `EXCLUDE USING gist` 제약을 추가해, 동일 resource의 시간대 겹침(BOOKED 상태)을 DB 레벨에서 차단합니다.

---

## 7) Idempotency-Key 동작 규칙
- 헤더 없음: 기존과 동일하게 일반 예약 생성
- 같은 `Idempotency-Key` + 같은 payload: 같은 예약 결과 재반환
- 같은 `Idempotency-Key` + 다른 payload: `409`
- 같은 `Idempotency-Key` 요청 처리 중 재호출: `409 (in progress)`

---

## 8) 인프라 (Infra)
```bash
docker compose up -d
```

---

## 9) 주요 API (Main Endpoints)
- `GET /health`
- `GET /ready`
- `POST /auth/signup`
- `POST /auth/login`
- `POST /resources` (admin)
- `GET /resources` (auth)
- `PATCH /resources/{resource_id}` (admin)
- `DELETE /resources/{resource_id}` (admin)
- `POST /reservations` (auth, optional `Idempotency-Key` header)
- `PATCH /reservations/{reservation_id}` (owner/admin)
- `GET /reservations` (auth)
- `POST /reservations/{reservation_id}/cancel` (owner/admin)

---

## 10) 표준 에러 응답 (Standard Error Body)
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

## 11) 프로젝트 구조 (Project Structure)
- `app/api/routes.py` : API 엔드포인트
- `app/core/security.py` : JWT, password hash
- `app/core/errors.py` : 전역 예외 응답 포맷
- `app/models.py` : User/Resource/Reservation/AuditLog
- `alembic/` : DB migration scripts
- `tests/` : API 테스트 코드
