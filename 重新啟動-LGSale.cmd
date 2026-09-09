@echo off
chcp 65001 >nul
title Restart LGSale

rem Administrator rights are required when the existing listener belongs to
rem an elevated process or a background task. Relaunch this file through UAC.
fltmc >nul 2>&1
if errorlevel 1 (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

rem Start-LGSale.ps1 reads this computer's .env.local, detects the configured
rem port, stops any existing listener, and starts LGSale in the background.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-LGSale.ps1" -Restart -Hidden
if errorlevel 1 (
    echo.
    echo LGSale restart failed. Review the error shown above.
    pause
    exit /b 1
)

echo.
echo LGSale restart command completed. This window can now be closed.
timeout /t 3 /nobreak >nul

