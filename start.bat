@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "DASHBOARD_URL=http://localhost:8501"
set "OLLAMA_URL=http://localhost:11434"
set "REQUIRED_MODEL=mistral"
set "MAX_WAIT_SECONDS=180"
set "MAX_DOCKER_WAIT_SECONDS=300"

echo.
echo ============================================================
echo   IPO Surge Intelligence - Docker Startup
echo ============================================================
echo.

REM --- 1. Docker CLI ---
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker CLI not found.
    echo         Install Docker Desktop: https://www.docker.com/products/docker-desktop/
    exit /b 1
)
echo [OK] Docker CLI found

REM --- 2. Docker daemon (auto-start Docker Desktop if needed) ---
call :ensure_docker_running
if errorlevel 1 exit /b 1
echo [OK] Docker daemon is running

REM --- 3. Docker Compose ---
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available.
    echo         Update Docker Desktop to a version that includes Compose V2.
    exit /b 1
)
echo [OK] Docker Compose available

REM --- 4. Port conflict warning ---
call :check_port 8501 "Streamlit dashboard"
call :check_port 11434 "Ollama API"

REM --- 5. Warn if native dev mode is running ---
if exist ".dev-streamlit.pid" (
    echo [WARN] Native dev mode appears to be running ^(.dev-streamlit.pid found^).
    echo        Stop it first with stop-dev.bat or stop.bat to avoid port conflicts.
    echo.
)

REM --- 6. Start stack ---
echo.
echo Starting Docker Compose stack ^(first run may take several minutes to build^)...
docker compose up -d --build
if errorlevel 1 (
    echo [ERROR] docker compose up failed.
    exit /b 1
)

REM --- 7. Wait for Ollama ---
echo.
echo Waiting for Ollama to become healthy...
set /a ELAPSED=0
:wait_ollama
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%OLLAMA_URL%/api/tags' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ollama_ready
if !ELAPSED! geq %MAX_WAIT_SECONDS% (
    echo [ERROR] Ollama did not become ready within %MAX_WAIT_SECONDS% seconds.
    echo         Check logs: docker logs raveminds_ollama
    exit /b 1
)
timeout /t 3 /nobreak >nul
set /a ELAPSED+=3
goto wait_ollama
:ollama_ready
echo [OK] Ollama is responding

REM --- 8. Ensure mistral model is pulled ---
echo.
echo Checking for '%REQUIRED_MODEL%' model in Ollama container...
docker exec raveminds_ollama ollama list 2>nul | findstr /i "%REQUIRED_MODEL%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Pulling '%REQUIRED_MODEL%' model ^(this may take several minutes on first run^)...
    docker exec raveminds_ollama ollama pull %REQUIRED_MODEL%
    if errorlevel 1 (
        echo [ERROR] Failed to pull '%REQUIRED_MODEL%' model.
        exit /b 1
    )
) else (
    echo [OK] '%REQUIRED_MODEL%' model already available
)

REM --- 9. Wait for Streamlit dashboard ---
echo.
echo Waiting for Streamlit dashboard...
set /a ELAPSED=0
:wait_dashboard
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%DASHBOARD_URL%' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto dashboard_ready
if !ELAPSED! geq %MAX_WAIT_SECONDS% (
    echo [ERROR] Dashboard did not become ready within %MAX_WAIT_SECONDS% seconds.
    echo         Check logs: docker logs raveminds_ipo_surge
    exit /b 1
)
timeout /t 3 /nobreak >nul
set /a ELAPSED+=3
goto wait_dashboard
:dashboard_ready
echo [OK] Dashboard is ready at %DASHBOARD_URL%

REM --- 10. Open browser ---
echo.
echo Opening dashboard in your default browser...
start "" "%DASHBOARD_URL%"

echo.
echo ============================================================
echo   Stack is UP
echo   Dashboard : %DASHBOARD_URL%
echo   Ollama    : %OLLAMA_URL%
echo   Stop with : stop.bat  ^(add --purge to wipe Ollama volume^)
echo ============================================================
echo.
exit /b 0

:check_port
set "PORT=%~1"
set "LABEL=%~2"
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port %PORT% ^(%LABEL%^) is already in use. Startup may fail if it is not this project.
)
exit /b 0

:ensure_docker_running
docker info >nul 2>&1
if not errorlevel 1 exit /b 0

echo [INFO] Docker Desktop is not running. Launching it now...

set "DOCKER_EXE="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
)
if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
)

if "!DOCKER_EXE!"=="" (
    echo [ERROR] Could not find Docker Desktop.exe.
    echo         Install Docker Desktop: https://www.docker.com/products/docker-desktop/
    exit /b 1
)

start "" "!DOCKER_EXE!"
echo [INFO] Waiting for Docker Desktop to be ready ^(may take 1-3 minutes on cold start^)...

set /a ELAPSED=0
:wait_docker
docker info >nul 2>&1
if not errorlevel 1 exit /b 0
if !ELAPSED! geq %MAX_DOCKER_WAIT_SECONDS% (
    echo [ERROR] Docker Desktop did not become ready within %MAX_DOCKER_WAIT_SECONDS% seconds.
    echo         Ensure WSL2 is enabled and Docker Desktop finished starting, then run start.bat again.
    exit /b 1
)
set /a MOD=!ELAPSED! %% 15
if !MOD! equ 0 if !ELAPSED! gtr 0 echo [INFO] Still waiting for Docker... ^(!ELAPSED!s^)
timeout /t 5 /nobreak >nul
set /a ELAPSED+=5
goto wait_docker
