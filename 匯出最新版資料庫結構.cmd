@echo off
setlocal
cd /d "%~dp0"
set "SQLPS=C:\Program Files (x86)\Microsoft SQL Server\160\Tools\Binn\SQLPS.exe"
if not exist "%SQLPS%" (
  echo SQLPS.exe was not found. Install SQL Server tools or update this path.
  pause
  exit /b 1
)
"%SQLPS%" -NoProfile -File ".\tools\Export-LGSaleSchema.ps1" -UseProjectEnvironment
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" (
  echo Export failed. Review the error above.
) else (
  echo Export completed. Check database\baseline\LGSaleOut_Schema.sql
)
pause
exit /b %RESULT%
