@echo off
chcp 65001 >nul
echo ====================================
echo     安心宝 PWA 前端启动
echo ====================================
echo.
echo 正在启动开发服务器...
echo.
cd /d %~dp0
npm run dev
pause
