@echo off
echo Switching from PostgreSQL 17 to PostgreSQL 15...
echo.
echo Stopping PostgreSQL 17...
net stop postgresql-x64-17
echo.
echo Starting PostgreSQL 15...
net start postgresql-x64-15
echo.
echo Done! PostgreSQL 15 is now running on port 5432
echo.
pause
