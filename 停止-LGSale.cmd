@echo off
chcp 65001 >nul
title Stop LGSale

rem Administrator rights are required when LGSale belongs to an elevated
rem process or background task. Relaunch this file through UAC when needed.
fltmc >nul 2>&1
if errorlevel 1 (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

rem Read this computer's .env.local and stop the listener on its configured
rem port. The -Stop mode exits without starting a replacement process.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-LGSale.ps1" -Stop
if errorlevel 1 (
    echo.
    echo LGSale stop failed. Review the error shown above.
    pause
    exit /b 1
)

echo.
echo LGSale is stopped and will not be restarted.
pause
