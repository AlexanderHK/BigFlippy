@echo off
echo ========================================
echo       FlipDisk System Launcher
echo ========================================
echo Starting FlipDisk backend and frontend...
echo.

REM Check if Python files exist
if not exist "FlipDisk.py" (
    echo ERROR: FlipDisk.py not found!
    echo Please run this from the FlipDisk directory.
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Please run this from the FlipDisk directory.
    pause
    exit /b 1
)

REM Start backend in new window
echo Starting FlipDisk backend...
start "FlipDisk Backend" cmd /k "python FlipDisk.py"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting Flask frontend...
start "FlipDisk Frontend" cmd /k "python app.py"

echo.
echo ========================================
echo FlipDisk system started successfully!
echo.
echo Backend: Running in separate window
echo Frontend: Running in separate window
echo Web interface: http://10.0.0.143:5000
echo.
echo Close both windows to stop the system.
echo ========================================
pause