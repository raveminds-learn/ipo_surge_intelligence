@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "PURGE=0"
if /i "%~1"=="--purge" set "PURGE=1"

echo.
echo ============================================================
echo   IPO Surge Intelligence - Shutdown
echo ============================================================
echo.

REM --- Stop native dev mode if running ---
if exist ".dev-streamlit.pid" (
    echo Stopping native dev Streamlit process...
    call "%~dp0stop-dev.bat"
    echo.
)

REM --- Docker Compose ---
where docker >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker CLI not found; skipping container shutdown.
    goto done
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker daemon not running; containers may already be stopped.
    goto done
)

if "%PURGE%"=="1" (
    echo Stopping containers and removing volumes ^(including Ollama model cache^)...
    docker compose down -v
    if errorlevel 1 (
        echo [ERROR] docker compose down -v failed.
        exit /b 1
    )
    echo [OK] Containers stopped and volumes purged.
    echo [INFO] Next start will re-pull the mistral model.
) else (
    echo Stopping containers ^(data volumes preserved^)...
    docker compose down
    if errorlevel 1 (
        echo [ERROR] docker compose down failed.
        exit /b 1
    )
    echo [OK] Containers stopped.
    echo [INFO] Seeded data in ./data and Ollama models volume are preserved.
)

:done
echo.
echo ============================================================
echo   Stack is DOWN
echo   Start again : start.bat       ^(Docker^)
echo                 start-dev.bat   ^(native dev^)
if "%PURGE%"=="0" (
    echo   Purge data  : stop.bat --purge
)
echo ============================================================
echo.
exit /b 0
