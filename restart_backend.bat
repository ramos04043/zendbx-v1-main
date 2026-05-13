@echo off
echo Stopping backend server...
taskkill /F /IM python.exe /T 2>nul

echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo Starting backend server...
cd backend
start cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Backend server restarted!
echo Check the new window for server logs.
pause
