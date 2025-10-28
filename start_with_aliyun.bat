@echo off
REM 使用阿里云百炼配置启动 GTPlanner 服务

echo ========================================
echo   GTPlanner - 使用阿里云百炼配置启动
echo ========================================

REM 设置阿里云百炼环境变量
set LLM_API_KEY=sk-88ed0cac1b698888b5a5b80375db6666
set LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
set LLM_MODEL=qwen-max

echo.
echo 环境变量已设置：
echo   LLM_API_KEY: sk-44ed0ca...
echo   LLM_BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1
echo   LLM_MODEL: qwen-max
echo.
echo 正在启动服务...
echo ========================================
echo.

REM 启动服务
python fastapi_main.py

