@echo off
chcp 65001 >nul
title FORM Studio - Dung Dashboard
echo ==================================================================
echo   FORM STUDIO - DỪNG HỆ THỐNG EXECUTIVE DASHBOARD
echo ==================================================================
powershell -ExecutionPolicy Bypass -File "%~dp0manage_app.ps1" -Action stop
echo.
pause
