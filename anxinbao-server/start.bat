@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   安心宝云端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [2/3] 安装依赖...
pip install -r requirements.txt -q

echo [3/3] 启动服务...
echo.
echo ----------------------------------------
echo   服务地址: http://localhost:8000
echo   按 Ctrl+C 停止服务
echo ----------------------------------------
echo.

python main.py

pause
