@echo off
setlocal enabledelayedexpansion

:: === LOAD ENV FILE (relative path from script directory) ===
for /f "tokens=1,2 delims==" %%A in (..\.env) do (
    set %%A=%%B
)

:: === DATE (YYYY-MM-DD) ===
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set DATE=%%c-%%a-%%b

:: === BACKUP FILE PATH ===
set BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_%DATE%.sql

:: === CREATE BACKUP DIRECTORY IF NOT EXISTS ===
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [%date% %time%] Starting backup for database: %DB_NAME%

:: === RUN BACKUP (no password needed, pgpass.conf handles it) ===
"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Backup successful: %BACKUP_FILE%
) else (
    echo [%date% %time%] Backup failed!
    del "%BACKUP_FILE%"
)

endlocal


