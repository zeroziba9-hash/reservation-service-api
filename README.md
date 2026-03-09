# fastapi-service-template

Production-minded FastAPI starter template.

## Included Features
- Health check endpoint
- JWT authentication (signup/login)
- Role-based authorization (first user becomes ADMIN)
- Overlap-safe reservation creation (409 on conflict)
- Reservation cancel flow (owner/admin)
- Pytest tests + GitHub Actions CI

## Stack
- FastAPI
- PostgreSQL (default infra) / SQLite (local quick start)
- Redis
- SQLAlchemy
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
