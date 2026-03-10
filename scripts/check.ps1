$ErrorActionPreference = 'Stop'

Write-Host '[1/4] Black format check...' -ForegroundColor Cyan
python -m black --check . | Out-Host

Write-Host '[2/4] Ruff lint check...' -ForegroundColor Cyan
python -m ruff check . | Out-Host

Write-Host '[3/4] Alembic migration check...' -ForegroundColor Cyan
python -m alembic upgrade head | Out-Host

Write-Host '[4/4] Pytest...' -ForegroundColor Cyan
python -m pytest -q | Out-Host
