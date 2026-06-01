<#
Start the MediConnect-AI stack locally in a production-like mode using Docker Compose.

Usage:
  - Copy `.env.example` to `.env` and fill required keys (SARVAM_API_KEY, ADMIN_SECRET_TOKEN, etc.)
  - From repository root run (PowerShell):
      .\scripts\start_local.ps1

This script will build and start the `backend`, `frontend`, and `redis` services.
#>

Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $root\.. | Out-Null

if (-not (Test-Path .env)) {
    Write-Host "No .env file found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env -Force
    Write-Host "Created .env. Please edit .env and set SARVAM_API_KEY and ADMIN_SECRET_TOKEN before continuing." -ForegroundColor Cyan
    Write-Host "Opening .env in default editor..." -ForegroundColor Cyan
    if ($env:EDITOR) { & $env:EDITOR .env } else { Start-Process notepad.exe .env }
    Read-Host "Press Enter after editing .env to continue or Ctrl+C to cancel"
}

# Build and start containers
Write-Host "Starting services with docker-compose..." -ForegroundColor Green
docker-compose up --build -d

Write-Host "Services started. Follow backend logs with: docker-compose logs -f backend" -ForegroundColor Green
Write-Host "To run the seed script inside the backend container (create demo accounts):" -ForegroundColor Cyan
Write-Host "  docker-compose exec backend python backend/scripts/seed_accounts.py" -ForegroundColor Cyan

Pop-Location | Out-Null