# 使用阿里云百炼配置启动 GTPlanner 服务

Write-Host "========================================"
Write-Host "  GTPlanner - 使用阿里云百炼配置启动"
Write-Host "========================================"
Write-Host ""

# 设置阿里云百炼环境变量
$env:LLM_API_KEY="sk-88ed0cac1b698888b5a5b80375db6666"
$env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:LLM_MODEL="qwen-max"

Write-Host "环境变量已设置："
Write-Host "  LLM_API_KEY: sk-44ed0ca..."
Write-Host "  LLM_BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1"
Write-Host "  LLM_MODEL: qwen-max"
Write-Host ""
Write-Host "正在启动服务..."
Write-Host "========================================"
Write-Host ""

# 启动服务
python fastapi_main.py

