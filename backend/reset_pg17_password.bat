@echo off
echo ========================================
echo PostgreSQL 17 Password Reset Helper
echo ========================================
echo.
echo This will reset the postgres user password for PostgreSQL 17
echo.
echo Step 1: Edit pg_hba.conf to allow trust authentication
echo Location: C:\Program Files\PostgreSQL\17\data\pg_hba.conf
echo.
echo Change this line:
echo   host    all             all             127.0.0.1/32            scram-sha-256
echo To:
echo   host    all             all             127.0.0.1/32            trust
echo.
echo Step 2: Restart PostgreSQL 17
echo   net stop postgresql-x64-17
echo   net start postgresql-x64-17
echo.
echo Step 3: Connect without password and reset it
echo   "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5433 -d postgres
echo   ALTER USER postgres WITH PASSWORD 'Pawan@121';
echo   \q
echo.
echo Step 4: Revert pg_hba.conf back to scram-sha-256
echo.
echo Step 5: Restart PostgreSQL 17 again
echo.
pause
