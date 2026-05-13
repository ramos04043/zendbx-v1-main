@echo off
echo ========================================
echo  Restarting PostgreSQL Service
echo ========================================
echo.
echo This will restart PostgreSQL to clear connection issues.
echo.
pause

echo Stopping PostgreSQL...
net stop postgresql-x64-17

echo Waiting 3 seconds...
timeout /t 3 /nobreak

echo Starting PostgreSQL...
net start postgresql-x64-17

echo.
echo ========================================
echo  PostgreSQL Restarted Successfully!
echo ========================================
echo.
echo You can now restart your backend server.
echo.
pause
