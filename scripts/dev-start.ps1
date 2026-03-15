# NyxAI Local Development Startup Script for PowerShell
# Usage: .\dev-start.ps1 [-Port 8000] [-Reload]

param(
    [int]$Port = 8000,
    [switch]$Reload
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "NyxAI Local Development Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Set default environment variables
$env:NYX_ENV = "development"
$env:NYX_DEBUG = "true"
$env:NYX_DB_URL = "sqlite+aiosqlite:///./data/nyxai.db"
$env:NYX_DB_ECHO = "false"
$env:NYX_VECTOR_ENABLED = "true"
$env:NYX_VECTOR_PERSIST_DIRECTORY = "./data/vector_db"
$env:NYX_VECTOR_COLLECTION_NAME = "incidents"
$env:NYX_LOG_LEVEL = "INFO"
$env:NYX_LOG_FORMAT = "console"
$env:PYTHONPATH = Join-Path $PSScriptRoot "..\src"

# Create data directory if not exists
$dataDir = Join-Path $PSScriptRoot "..\data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-Host "Created data directory: $dataDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "Environment configured:" -ForegroundColor Yellow
Write-Host "  NYX_ENV = $env:NYX_ENV"
Write-Host "  NYX_DEBUG = $env:NYX_DEBUG"
Write-Host "  NYX_DB_URL = $env:NYX_DB_URL"
Write-Host "  NYX_VECTOR_ENABLED = $env:NYX_VECTOR_ENABLED"
Write-Host ""

# Build uvicorn command
$uvicornArgs = @(
    "-m", "uvicorn",
    "nyxai.api.main:app",
    "--host", "0.0.0.0",
    "--port", $Port
)

if ($Reload) {
    $uvicornArgs += "--reload"
    $uvicornArgs += "--reload-dir"
    $uvicornArgs += "src/nyxai"
}

Write-Host "Starting server on http://localhost:$Port" -ForegroundColor Green
Write-Host "API docs: http://localhost:$Port/docs" -ForegroundColor Green
Write-Host "Health check: http://localhost:$Port/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Change to project root
$projectRoot = Join-Path $PSScriptRoot ".."
Set-Location $projectRoot

try {
    & python @uvicornArgs
}
catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Server stopped" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
