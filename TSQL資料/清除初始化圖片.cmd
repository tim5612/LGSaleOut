@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Clear-InitializationPhotos.ps1" %*
exit /b %errorlevel%
