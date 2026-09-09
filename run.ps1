<#
    ArthSanchay — local run script.

    Sets up the backend virtual environment and the frontend production build on first run
    (skipped on later runs once they already exist), then starts the app as a single process at
    http://localhost:8000. Press Ctrl+C to stop.

    Usage (from a PowerShell prompt, from anywhere):
        .\run.ps1
    Double-clicking a .ps1 file does not execute it by default on Windows — run it from a
    terminal as above, or right-click it and choose "Run with PowerShell".
#>

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"
$staticIndex = Join-Path $backend "app\static\index.html"

Write-Host "== ArthSanchay: local run ==" -ForegroundColor Cyan

# --- Backend: create the virtual environment and install dependencies on first run ---
if (-not (Test-Path $venvPython)) {
    Write-Host "No backend virtual environment found -- setting one up (first run only)..." -ForegroundColor Yellow
    Push-Location $backend
    python -m venv .venv
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
    Pop-Location
}

# --- Frontend: build the SPA if it hasn't been built yet ---
if (-not (Test-Path $staticIndex)) {
    Write-Host "No frontend build found -- building it (first run only)..." -ForegroundColor Yellow
    Push-Location $frontend
    npm install
    npm run build
    Pop-Location
}

# --- Start the server (also runs pending database migrations on startup) ---
Write-Host ""
Write-Host "Starting ArthSanchay at http://localhost:8000  (Ctrl+C to stop)" -ForegroundColor Green
Push-Location $backend
try {
    & $venvPython -m uvicorn app.main:app --port 8000
}
finally {
    Pop-Location
}
