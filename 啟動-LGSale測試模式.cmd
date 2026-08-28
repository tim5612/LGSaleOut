@echo off
chcp 65001 >nul
title LGSale 測試服務
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Restart-LGSale-Dev.ps1"
