@echo off
chcp 65001 >nul
echo ====================================
echo GTPlanner 启动脚本
echo ====================================
echo.

REM 检查 Python 版本
python --version
if %errorlevel% neq 0 (
    echo [错误] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

echo.
echo [1/3] 检查依赖...
python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'" 2>nul
if %errorlevel% neq 0 (
    echo [警告] Python 版本低于 3.11，可能出现兼容性问题
    echo 建议升级到 Python 3.11+
)

python -c "import openai, fastapi, rich, pocketflow" 2>nul
if %errorlevel% neq 0 (
    echo [警告] 部分依赖缺失，正在安装...
    pip install -q openai fastapi rich pocketflow pocketflow-tracing pocketflow-agui
)

echo.
echo [2/3] 检查环境变量...
if "%LLM_API_KEY%"=="" (
    echo [警告] 未设置 LLM_API_KEY 环境变量
    echo 请设置以下环境变量:
    echo   set LLM_API_KEY=your-api-key
    echo   set LLM_BASE_URL=https://api.openai.com/v1
    echo   set LLM_MODEL=gpt-4
    echo.
    echo 或创建 .env 文件（推荐）
)

echo.
echo [3/3] 启动 GTPlanner...
echo.
echo 请选择启动模式:
echo   1) 启动 CLI 模式
echo   2) 启动 FastAPI 服务
echo   3) 启动 MCP 服务
echo.

set /p choice="请输入选项 (1/2/3): "

if "%choice%"=="1" (
    python gtplanner.py
) else if "%choice%"=="2" (
    python fastapi_main.py
) else if "%choice%"=="3" (
    cd mcp
    python mcp_service.py
) else (
    echo 无效选项
    pause
    exit /b 1
)

pause

