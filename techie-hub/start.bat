@echo off
setlocal EnableDelayedExpansion

set "FORCE_RESTART=0"
if /I "%~1"=="force" set "FORCE_RESTART=1"
if /I "%~1"=="--force" set "FORCE_RESTART=1"
if /I "%~1"=="/force" set "FORCE_RESTART=1"

echo ============================================
echo   TECHIE HUB - Azure0429 Launcher
echo ============================================
echo.
if "!FORCE_RESTART!"=="1" (
    echo   Mode: FORCE RESTART
    echo.
)

set "HEADLESS=1"
set "HUB_DIR=%~dp0"
for %%I in ("%~dp0..\notecode") do set "NOTECODE_DIR=%%~fI"
for %%I in ("%~dp0..\aio2-main") do set "AIO_DIR=%%~fI"
for %%I in ("%~dp0..\kotomegane") do set "KOTOMEGANE_DIR=%%~fI"
set "LOG_DIR=%HUB_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul

set "HUB_PORT=8090"
set "HUB_URL=http://127.0.0.1:%HUB_PORT%/"
set "HUB_CACHE_BUST=%RANDOM%"
set "HUB_OPEN_URL=%HUB_URL%?v=%HUB_CACHE_BUST%"
set "KM_URL=http://127.0.0.1:8083/healthz"
set "HUB_PY=%NOTECODE_DIR%\.venv\Scripts\python.exe"
set "HUB_PY_ARGS="
set "KM_RUN=%KOTOMEGANE_DIR%\run.ps1"
set "KM_STOP=%KOTOMEGANE_DIR%\stop.ps1"
if not exist "%HUB_PY%" (
    set "HUB_PY=py"
    set "HUB_PY_ARGS=-3.11"
)

if "!FORCE_RESTART!"=="1" call :stop_port 8090 "TECHIE HUB"
netstat -an 2>nul | findstr ":!HUB_PORT! " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   [1/5] TECHIE HUB - already running
) else (
    echo   [1/5] TECHIE HUB - starting...
    echo Using: !HUB_PY! !HUB_PY_ARGS! > "%LOG_DIR%\hub.log"
    start "TechieHub" /D "%HUB_DIR%" /B cmd /c ""!HUB_PY!" !HUB_PY_ARGS! -m http.server !HUB_PORT! --bind 127.0.0.1 >> "%LOG_DIR%\hub.log" 2>&1"
)

set PORT=8080
if "!FORCE_RESTART!"=="1" call :stop_port 8080 "Kotomake"
netstat -an 2>nul | findstr ":8080 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   [2/5] Kotomake - already running
) else (
    echo   [2/5] Kotomake - starting...
    set "NOTECODE_PY=%NOTECODE_DIR%\.venv\Scripts\python.exe"
    set "NOTECODE_PY_ARGS="
    if not exist "!NOTECODE_PY!" (
        set "NOTECODE_PY=py"
        set "NOTECODE_PY_ARGS=-3.11"
    )
    echo Using: !NOTECODE_PY! !NOTECODE_PY_ARGS! > "%LOG_DIR%\kotomake.log"
    start "Kotomake" /D "%NOTECODE_DIR%" /B cmd /c ""!NOTECODE_PY!" !NOTECODE_PY_ARGS! run_kotomake.py >> "%LOG_DIR%\kotomake.log" 2>&1"
)

timeout /t 1 /nobreak >nul

set PORT=8081
if "!FORCE_RESTART!"=="1" call :stop_port 8081 "Kotomigaki"
netstat -an 2>nul | findstr ":8081 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   [3/5] Kotomigaki - already running
) else (
    echo   [3/5] Kotomigaki - starting...
    set "AIO_PY=%AIO_DIR%\.venv\Scripts\python.exe"
    set "AIO_PY_ARGS="
    if not exist "!AIO_PY!" (
        set "AIO_PY=py"
        set "AIO_PY_ARGS=-3.11"
    )
    echo Using: !AIO_PY! !AIO_PY_ARGS! > "%LOG_DIR%\kotomigaki.log"
    start "Kotomigaki" /D "%AIO_DIR%" /B cmd /c ""!AIO_PY!" !AIO_PY_ARGS! run_app.py >> "%LOG_DIR%\kotomigaki.log" 2>&1"
)

set PORT=8083
if "!FORCE_RESTART!"=="1" (
    if exist "!KM_STOP!" (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "!KM_STOP!" -Port 8083 >nul 2>&1
    ) else (
        call :stop_port 8083 "Kotomegane"
    )
)
netstat -an 2>nul | findstr ":8083 " | findstr "LISTENING" >nul 2>&1
set "KM_SHOULD_START=0"
if !ERRORLEVEL! EQU 0 (
    call :check_http "!KM_URL!"
    if !ERRORLEVEL! EQU 0 (
        echo   [4/5] Kotomegane - already running
    ) else (
        echo   [4/5] Kotomegane - unresponsive listener detected, restarting...
        if exist "!KM_STOP!" (
            powershell.exe -NoProfile -ExecutionPolicy Bypass -File "!KM_STOP!" -Port 8083 >nul 2>&1
        ) else (
            call :stop_port 8083 "Kotomegane"
        )
        set "KM_SHOULD_START=1"
    )
) else (
    set "KM_SHOULD_START=1"
)
if "!KM_SHOULD_START!"=="1" (
    if not exist "!KM_RUN!" (
        echo   [4/5] Kotomegane - run.ps1 not found
    ) else (
        echo   [4/5] Kotomegane - starting...
        echo Using: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "!KM_RUN!" > "%LOG_DIR%\kotomegane.log"
        start "Kotomegane" /D "!KOTOMEGANE_DIR!" /B cmd /c ""powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "!KM_RUN!" >> "%LOG_DIR%\kotomegane.log" 2>&1"
        call :wait_http "!KM_URL!" "Kotomegane" 20
    )
)

echo   [5/5] Waiting for servers...
timeout /t 5 /nobreak >nul

echo   Opening TOP page...
start "" "%HUB_OPEN_URL%"
echo   Logs: %LOG_DIR%\hub.log, %LOG_DIR%\kotomake.log, %LOG_DIR%\kotomigaki.log, %LOG_DIR%\kotomegane.log

echo.
echo ============================================
echo   Done - check in your browser
echo ============================================
pause
goto :eof

:stop_port
echo   - %~2 (port %~1): reset...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%~1 " ^| findstr "LISTENING"') do (
    if not "%%P"=="0" (
        taskkill /PID %%P /F >nul 2>&1
    )
)
timeout /t 1 /nobreak >nul
exit /b 0

:check_http
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; try { $resp = Invoke-WebRequest -UseBasicParsing '%~1' -TimeoutSec 5; if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { exit 0 } } catch { } exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:wait_http
setlocal EnableDelayedExpansion
set "TARGET_URL=%~1"
set "TARGET_LABEL=%~2"
set "MAX_TRIES=%~3"
if "!MAX_TRIES!"=="" set "MAX_TRIES=20"
for /L %%I in (1,1,!MAX_TRIES!) do (
    call :check_http "!TARGET_URL!"
    if !ERRORLEVEL! EQU 0 (
        endlocal & exit /b 0
    )
    timeout /t 1 /nobreak >nul
)
echo   - !TARGET_LABEL! health check timed out
endlocal & exit /b 1
