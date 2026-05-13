@echo off
echo ========================================
echo Restarting Backend Server
echo ========================================
echo.

echo Stopping any running Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend server...
cd backend
start cmd /k "python -m uvicorn app.main:app --reload --port 8000"

echo.
echo ========================================
echo Backend server is restarting!
echo ========================================
echo.
echo The backend will be available at:
echo http://localhost:8000
echo.
echo API docs at:
echo http://localhost:8000/docs
echo.
pause
