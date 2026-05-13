@echo off
echo Making PostgreSQL 15 the permanent default...
echo.

echo Step 1: Stop PostgreSQL 17
net stop postgresql-x64-17

echo Step 2: Set PostgreSQL 17 to Manual startup (won't auto-start)
sc config postgresql-x64-17 start= demand

echo Step 3: Start PostgreSQL 15
net start postgresql-x64-15

echo Step 4: Set PostgreSQL 15 to Automatic startup (starts on boot)
sc config postgresql-x64-15 start= auto

echo.
echo ✅ Done! PostgreSQL 15 is now your permanent default database.
echo    - PostgreSQL 15: Auto-starts on Windows boot
echo    - PostgreSQL 17: Manual start only (disabled auto-start)
echo.
pause