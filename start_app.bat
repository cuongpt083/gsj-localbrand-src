@echo off
chcp 65001 >nul
title FORM Studio - Khoi Dong Dashboard
echo ==================================================================
echo   FORM STUDIO - KHỞI ĐỘNG HỆ THỐNG EXECUTIVE DASHBOARD
echo ==================================================================
powershell -ExecutionPolicy Bypass -File "%~dp0manage_app.ps1" -Action start
echo.
pause
