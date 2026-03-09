# fastapi-service-template

Production-minded FastAPI starter template.

## Included Features
- Health check endpoint
- JWT authentication (signup/login)
- Role-based authorization (first user becomes ADMIN)
- Overlap-safe reservation creation (409 on conflict)
- Reservation cancel flow (owner/admin)
- Reservation filter query (`status`, `resource_id`, `from_at`, `to_at`)
- Audit log write on signup/resource create/reservation create/cancel
- Standardized error response format
- Alembic migration baseline
- Pytest tests + GitHub Actions CI

## Stack
- FastAPI
- PostgreSQL (default infra) / SQLite (local quick start)
- Redis
- SQLAlchemy
- Alembic
- Pytest
- GitHub Actions

## Run
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test
```bash
pytest -q
```

## Migration
```bash
alembic upgrade head
```

## Infra
```bash
docker compose up -d
```

## Main Endpoints
- `GET /health`
- `POST /auth/signup`
- `POST /auth/login`
- `POST /resources` (admin only)
- `POST /reservations` (auth required)
- `GET /reservations` (auth required)
- `POST /reservations/{reservation_id}/cancel` (owner/admin)

## Standard Error Body
```json
{
  "timestamp": "2026-03-09T14:00:00Z",
  "status": 409,
  "code": "HTTP_ERROR",
  "message": "time slot already booked",
  "detail": []
}
```
