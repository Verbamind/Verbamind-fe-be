# VerbaMind Setup Script
# Run this to create virtual environment and install all dependencies
# PowerShell: .\setup.ps1

param(
    [switch]$SkipGUI = $false
)

$ErrorActionPreference = "Stop"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VerbaMind Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "`n[1/5] Creating virtual environment..."
if (Test-Path ".venv") {
    Write-Host "  .venv already exists, skipping" -ForegroundColor Gray
} else {
    python -m venv .venv
    Write-Host "  .venv created" -ForegroundColor Green
}

Write-Host "`n[2/5] Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

Write-Host "`n[3/5] Upgrading pip..."
pip install --upgrade pip --quiet

Write-Host "`n[4/5] Installing core dependencies..."
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite pydantic pydantic-settings httpx alembic pycryptodome pywin32 pytest pytest-asyncio pytest-cov

Write-Host "`n[5/5] Installing project in development mode..."
pip install -e .

if (-not $SkipGUI) {
    Write-Host "`n[Optional] Installing GUI dependencies..."
    pip install PySide6
}

Write-Host "`n[Optional] AI pipeline dependencies (large downloads):"
Write-Host "  pip install openai-whisper torch transformers llama-cpp-python"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup complete! Run: pytest" -ForegroundColor Green
Write-Host "Backend: python -m verbamind.backend.main" -ForegroundColor Green
Write-Host "GUI:     python -m verbamind.main" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
