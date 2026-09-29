@echo off
chcp 65001 >nul
setlocal
echo.
echo ==============================================
echo   胸影智诊 V3.0 - 环境配置 (纯 CPU 版本)
echo   不使用 Conda / CUDA，仅 venv + CPU 推理
echo ==============================================
echo.

cd /d "%~dp0backend"

:: 选择 Python 解释器 (优先系统 py 启动器，其次 python 命令)
set "PY_CMD="
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3.11"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
    ) else (
        echo [错误] 未找到 Python，请先安装 Python 3.10 / 3.11
        pause
        exit /b 1
    )
)

echo [步骤1] 创建虚拟环境 backend\venv ...
if not exist "venv\Scripts\python.exe" (
    %PY_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境已创建
) else (
    echo [提示] 虚拟环境已存在，跳过创建
)

echo.
echo [步骤2] 安装 CPU 版依赖 (首次约需 3-8 分钟) ...
echo.
venv\Scripts\python.exe -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ==============================================
echo [成功] 环境配置完成!
echo.
echo  环境位置 : backend\venv
echo  推理设备 : CPU (AI_DEVICE=cpu)
echo  数据库   : SQLite (backend\data\aixray.db)
echo.
echo  启动后端: start_backend.bat
echo  启动前端: cd frontend ^&^& npm run dev
echo ==============================================
pause
