@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist ".dev-streamlit.pid" (
    echo [INFO] No dev Streamlit process tracked ^(.dev-streamlit.pid not found^).
    exit /b 0
)

set /p PID=<".dev-streamlit.pid"
if "%PID%"=="" (
    echo [WARN] PID file is empty; removing stale file.
    del /f /q ".dev-streamlit.pid" 2>nul
    exit /b 0
)

echo Stopping Streamlit dev process ^(PID %PID%^)...
taskkill /PID %PID% /T /F >nul 2>&1
if errorlevel 1 (
    echo [WARN] Process %PID% was not running ^(may have already exited^).
) else (
    echo [OK] Streamlit dev process stopped.
)

del /f /q ".dev-streamlit.pid" 2>nul
exit /b 0
