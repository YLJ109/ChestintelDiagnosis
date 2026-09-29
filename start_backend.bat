@echo off
chcp 65001 >nul
setlocal
echo.
echo ==============================================
echo   胸影智诊 V3.0 - 后端启动 (CPU 推理)
echo   AIX-Ray Intelligent Diagnosis System
echo ==============================================
echo.

cd /d "%~dp0backend"

:: 运行环境
set "FLASK_ENV=development"
set "AI_DEVICE=cpu"
set "ORT_LOGGING_LEVEL=3"
set "PYTHONIOENCODING=utf-8"

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境 backend\venv
    echo        请先运行 setup_env.bat 创建环境并安装依赖
    pause
    exit /b 1
)

echo [信息] 虚拟环境   : backend\venv
echo [信息] 推理设备   : CPU (无 CUDA)
echo [信息] 数据库     : SQLite - backend\data\aixray.db
echo [信息] 服务地址   : http://localhost:5000
echo [提示] 按 Ctrl+C 停止服务
echo.

venv\Scripts\python.exe app.py

echo.
echo [停止] 后端服务已停止
pause
