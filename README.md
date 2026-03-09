# fastapi-service-template

Production-minded FastAPI starter template.

## Stack
- FastAPI
- PostgreSQL
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
