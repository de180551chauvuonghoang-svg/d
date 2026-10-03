@echo off
title AI XAUUSD Scalper Pro - Forward Testing System
color 0A
chcp 65001 >nul

echo ======================================================================
echo    KHỞI ĐỘNG HỆ THỐNG FORWARD TESTING AI SCALPER XAUUSD (1-CLICK)
echo ======================================================================
echo  * Đang khởi động Backend FastAPI + MT5 Bridge
echo  * Đang kích hoạt Bot Trade tự động
echo  * Đang mở Giao diện Web Dashboard TypeScript tại: http://127.0.0.1:8000
echo ======================================================================
echo.

set PYTHONUTF8=1
python run.py

pause
