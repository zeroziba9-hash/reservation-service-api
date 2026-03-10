$ErrorActionPreference = 'Stop'

Write-Host '[1/3] Installing dependencies (if needed)...' -ForegroundColor Cyan
python -m pip install -r requirements.txt | Out-Host

Write-Host '[2/3] Applying migrations...' -ForegroundColor Cyan
python -m alembic upgrade head | Out-Host

Write-Host '[3/3] Starting API server...' -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
