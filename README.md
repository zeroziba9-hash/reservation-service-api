# fastapi-service-template

Production-minded FastAPI starter template.

## Included Features
- Health check endpoint
- User/Resource/Reservation CRUD skeleton
- Overlap-safe reservation creation (409 on conflict)
- Reservation cancel flow
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
- `POST /users`
- `POST /resources`
- `POST /reservations`
- `GET /reservations`
- `POST /reservations/{reservation_id}/cancel`
