@echo off
chcp 65001 >nul
title LGSale
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-LGSale.ps1"
pause
