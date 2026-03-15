@echo off
chcp 65001 >nul
REM NyxAI Local Development Startup Script for Windows
REM Usage: dev-start.bat [port] [--reload]

echo ============================================================
echo NyxAI Local Development Startup
echo ============================================================

REM Set default environment variables
set "NYX_ENV=development"
set "NYX_DEBUG=true"
set "NYX_DB_URL=sqlite+aiosqlite:///./data/nyxai.db"
set "NYX_DB_ECHO=false"
set "NYX_VECTOR_ENABLED=true"
set "NYX_VECTOR_PERSIST_DIRECTORY=./data/vector_db"
set "NYX_VECTOR_COLLECTION_NAME=incidents"
set "NYX_LOG_LEVEL=INFO"
set "NYX_LOG_FORMAT=console"
set "PYTHONPATH=%~dp0..\src"

REM Create data directory if not exists
if not exist "data" mkdir data

REM Parse arguments
set PORT=8000
set RELOAD=

:parse_args
if "%~1"=="" goto :start_server
if "%~1"=="--reload" (
    set RELOAD=--reload
    shift
    goto :parse_args
)
if "%~1"=="-r" (
    set RELOAD=--reload
    shift
    goto :parse_args
)
set PORT=%~1
shift
goto :parse_args

:start_server
echo.
echo Starting server on http://localhost:%PORT%
echo API docs: http://localhost:%PORT%/docs
echo Health check: http://localhost:%PORT%/health
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn nyxai.api.main:app --host 0.0.0.0 --port %PORT% %RELOAD% --reload-dir src/nyxai

echo.
echo Server stopped
echo ============================================================
