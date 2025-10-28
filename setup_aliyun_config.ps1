# 阿里云百炼配置脚本

$env:LLM_API_KEY="sk-88ed0cac1b698888b5a5b80375db6666"
$env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:LLM_MODEL="qwen-max"

Write-Host "========================================"
Write-Host "  阿里云百炼配置完成"
Write-Host "========================================"
Write-Host "LLM_API_KEY: 已设置"
Write-Host "LLM_BASE_URL: $env:LLM_BASE_URL"
Write-Host "LLM_MODEL: $env:LLM_MODEL"
Write-Host ""
Write-Host "现在可以启动服务："
Write-Host "  python fastapi_main.py"
Write-Host "========================================"

