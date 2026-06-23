@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "DASHBOARD_URL=http://localhost:8501"
set "OLLAMA_URL=http://localhost:11434"
set "REQUIRED_MODEL=mistral"
set "MAX_WAIT_SECONDS=120"
set "PYTHON=python"

echo.
echo ============================================================
echo   IPO Surge Intelligence - Native Dev Startup
echo ============================================================
echo.

REM --- 1. Python ---
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found.
        echo         Install Python 3.11+ from https://www.python.org/downloads/
        exit /b 1
    )
    set "PYTHON=py -3"
)
echo [OK] Python found

REM --- 2. Python version >= 3.11 ---
for /f "tokens=2 delims= " %%v in ('%PYTHON% --version 2^>^&1') do set "PYVER=%%v"
echo [INFO] Python version: %PYVER%
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 or newer is required.
    exit /b 1
)
echo [OK] Python version meets requirement ^(3.11+^)

REM --- 3. Virtual environment ---
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment in .venv ...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)
echo [OK] Virtual environment ready

REM --- 4. Install dependencies ---
echo.
echo Installing / updating Python dependencies...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] pip install failed.
    exit /b 1
)
echo [OK] Dependencies installed

REM --- 5. Ollama CLI ---
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama CLI not found.
    echo         Install Ollama from https://ollama.com and ensure it is on your PATH.
    exit /b 1
)
echo [OK] Ollama CLI found

REM --- 6. Ollama service ---
echo.
echo Waiting for Ollama service...
set /a ELAPSED=0
:wait_ollama
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%OLLAMA_URL%/api/tags' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ollama_ready
if !ELAPSED! geq %MAX_WAIT_SECONDS% (
    echo [ERROR] Ollama is not responding on %OLLAMA_URL%
    echo         Start the Ollama application, then run start-dev.bat again.
    exit /b 1
)
if !ELAPSED! equ 0 (
    echo [INFO] If Ollama is not running, launch the Ollama app from the Start menu.
)
timeout /t 3 /nobreak >nul
set /a ELAPSED+=3
goto wait_ollama
:ollama_ready
echo [OK] Ollama service is responding

REM --- 7. Mistral model ---
echo.
echo Checking for '%REQUIRED_MODEL%' model...
ollama list 2>nul | findstr /i "%REQUIRED_MODEL%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Pulling '%REQUIRED_MODEL%' model ^(first run may take several minutes^)...
    ollama pull %REQUIRED_MODEL%
    if errorlevel 1 (
        echo [ERROR] Failed to pull '%REQUIRED_MODEL%' model.
        exit /b 1
    )
) else (
    echo [OK] '%REQUIRED_MODEL%' model already available
)

REM --- 8. Port conflict warning ---
call :check_port 8501 "Streamlit dashboard"
docker ps --filter "name=raveminds_ipo_surge" --filter "status=running" -q 2>nul | findstr /r "." >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Docker stack appears to be running. Stop it with stop.bat to avoid port conflicts.
)

REM --- 9. Seed data ---
echo.
echo Seeding LanceDB and DuckDB...
python scripts\seed_data.py
if errorlevel 1 (
    echo [ERROR] seed_data.py failed.
    exit /b 1
)
echo [OK] Data seeded

REM --- 10. Stop any previous dev instance ---
if exist ".dev-streamlit.pid" (
    echo [INFO] Stopping previous dev Streamlit instance...
    call "%~dp0stop-dev.bat" >nul 2>&1
)

REM --- 11. Start Streamlit in background ---
echo.
echo Starting Streamlit dashboard...
powershell -NoProfile -Command ^
    "$p = Start-Process -FilePath '%CD%\.venv\Scripts\python.exe' -ArgumentList '-m','streamlit','run','ui/app.py','--server.port=8501','--server.address=localhost' -WorkingDirectory '%CD%' -WindowStyle Minimized -PassThru; $p.Id | Out-File -FilePath '%CD%\.dev-streamlit.pid' -Encoding ascii -NoNewline"
if errorlevel 1 (
    echo [ERROR] Failed to start Streamlit.
    exit /b 1
)

REM --- 12. Wait for dashboard ---
echo Waiting for dashboard...
set /a ELAPSED=0
:wait_dashboard
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%DASHBOARD_URL%' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto dashboard_ready
if !ELAPSED! geq %MAX_WAIT_SECONDS% (
    echo [ERROR] Dashboard did not become ready within %MAX_WAIT_SECONDS% seconds.
    call "%~dp0stop-dev.bat"
    exit /b 1
)
timeout /t 2 /nobreak >nul
set /a ELAPSED+=2
goto wait_dashboard
:dashboard_ready
echo [OK] Dashboard is ready at %DASHBOARD_URL%

REM --- 13. Open browser ---
echo.
echo Opening dashboard in your default browser...
start "" "%DASHBOARD_URL%"

echo.
echo ============================================================
echo   Dev stack is UP
echo   Dashboard : %DASHBOARD_URL%
echo   Ollama    : %OLLAMA_URL%
echo   Stop with : stop-dev.bat
echo   Docker    : use start.bat / stop.bat instead
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
