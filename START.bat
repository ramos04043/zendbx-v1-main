@echo off
echo ========================================
echo   Nexora AI - Starting Application
echo ========================================
echo.

echo [1/2] Starting Backend (FastAPI)...
start "Nexora Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (Next.js)...
start "Nexora Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Application Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window...
pause >nul
