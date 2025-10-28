#!/bin/bash
set -e

echo "===================================="
echo "GTPlanner 启动脚本"
echo "===================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
echo "[1/3] 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] Python 3 未安装${NC}"
    exit 1
fi

python3 --version

# 检查 Python 版本
python3 -c "import sys; assert sys.version_info >= (3, 11)" 2>/dev/null || {
    echo -e "${YELLOW}[警告] Python 版本低于 3.11${NC}"
}

# 检查依赖
echo ""
echo "[2/3] 检查依赖..."
python3 -c "import openai, fastapi, rich, pocketflow" 2>/dev/null || {
    echo -e "${YELLOW}[警告] 部分依赖缺失，正在安装...${NC}"
    pip3 install -q openai fastapi rich pocketflow pocketflow-tracing pocketflow-agui
}

# 检查环境变量
echo ""
echo "[3/3] 检查环境变量..."
if [ -z "$LLM_API_KEY" ]; then
    echo -e "${YELLOW}[警告] 未设置 LLM_API_KEY 环境变量${NC}"
    echo "请设置以下环境变量:"
    echo "  export LLM_API_KEY=your-api-key"
    echo "  export LLM_BASE_URL=https://api.openai.com/v1"
    echo "  export LLM_MODEL=gpt-4"
    echo ""
    echo "或创建 .env 文件（推荐）"
fi

# 选择启动模式
echo ""
echo "请选择启动模式:"
echo "  1) 启动 CLI 模式"
echo "  2) 启动 FastAPI 服务"
echo "  3) 启动 MCP 服务"
echo ""

read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        python3 gtplanner.py
        ;;
    2)
        python3 fastapi_main.py
        ;;
    3)
        cd mcp
        python3 mcp_service.py
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

