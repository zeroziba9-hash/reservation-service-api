$ErrorActionPreference = 'Stop'

Write-Host '[1/4] Starting PostgreSQL + Redis containers...' -ForegroundColor Cyan
docker compose up -d | Out-Host

Write-Host '[2/4] Setting local Postgres environment...' -ForegroundColor Cyan
$env:DATABASE_URL = 'postgresql+psycopg2://app:app@127.0.0.1:5432/appdb'
$env:REDIS_URL = 'redis://127.0.0.1:6379/0'

Write-Host '[3/4] Applying migrations to PostgreSQL...' -ForegroundColor Cyan
python -m alembic upgrade head | Out-Host

Write-Host '[4/4] Starting API server (PostgreSQL)...' -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
