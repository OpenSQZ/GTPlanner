# GTPlanner 快速启动指南

## 📋 前提条件

### 必需项
- **Python 3.11+** (推荐 3.11 或更高版本)
- **pip** 或 **uv** 包管理器
- **LLM API Key** (OpenAI, Anthropic, Azure OpenAI 等兼容 API)

### 推荐
- Git
- IDE (VSCode, PyCharm 等)
- 虚拟环境 (venv, conda)

---

## 🚀 快速启动 (3 步骤)

### 步骤 1: 克隆项目

```bash
git clone https://github.com/OpenSQZ/GTPlanner.git
cd GTPlanner
```

### 步骤 2: 配置环境变量

#### 方式 A: 使用 .env 文件 (推荐)

创建 `.env` 文件:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置:

```env
# 核心配置（必需）
LLM_API_KEY="sk-your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"

# 可选配置
JINA_API_KEY="your-jina-key"
LANGFUSE_SECRET_KEY="your-secret-key"
LANGFUSE_PUBLIC_KEY="your-public-key"
LANGFUSE_HOST="https://cloud.langfuse.com"
```

#### 方式 B: 设置环境变量

**Windows PowerShell:**
```powershell
$env:LLM_API_KEY="sk-your-key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4"
```

**Windows CMD:**
```cmd
set LLM_API_KEY=sk-your-key
set LLM_BASE_URL=https://api.openai.com/v1
set LLM_MODEL=gpt-4
```

**Linux/Mac:**
```bash
export LLM_API_KEY="sk-your-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4"
```

### 步骤 3: 启动项目

#### 选项 A: 使用启动脚本 (最简单)

**Windows:**
```bash
start_windows.bat
```

**Linux/Mac:**
```bash
chmod +x start_linux.sh
./start_linux.sh
```

#### 选项 B: 手动启动

**1. 安装依赖**
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

**2. 选择启动模式**

**CLI 模式:**
```bash
python gtplanner.py
# 或
python gtplanner.py "设计一个用户管理系统"
```

**FastAPI 服务:**
```bash
uv run fastapi_main.py
# 服务运行在 http://0.0.0.0:11211
# 文档: http://0.0.0.0:11211/docs
```

**MCP 服务:**
```bash
cd mcp
uv sync
uv run python mcp_service.py
```

---

## ⚙️ 常用配置示例

### OpenAI 官方 API
```env
LLM_API_KEY="sk-proj-..."
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"
```

### Azure OpenAI
```env
LLM_API_KEY="your-azure-key"
LLM_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
LLM_MODEL="gpt-4"
```

### Anthropic Claude (通过代理)
```env
LLM_API_KEY="sk-ant-..."
LLM_BASE_URL="https://proxy.example.com/v1"
LLM_MODEL="claude-3-opus"
```

### 本地部署模型
```env
LLM_API_KEY="local-key"
LLM_BASE_URL="http://localhost:8000/v1"
LLM_MODEL="your-local-model"
```

### 国内代理服务
```env
LLM_API_KEY="your-proxy-key"
LLM_BASE_URL="https://your-proxy-provider.com/v1"
LLM_MODEL="gpt-4"
```

---

## 🔧 故障排查

### 问题 1: Python 版本不兼容

**错误信息:**
```
requires Python 3.11+, but you have 3.10.x
```

**解决方案:**
1. 升级 Python 到 3.11+
2. 或调整项目兼容 Python 3.10 (不推荐)

### 问题 2: 依赖安装失败

**错误信息:**
```
ERROR: pip subprocess to install build dependencies did not run successfully
```

**解决方案:**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用清华镜像 (中国大陆)
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

### 问题 3: 模块导入错误

**错误信息:**
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案:**
```bash
# 检查是否在项目根目录
pwd  # 应该是 .../GTPlanner

# 重新安装依赖
pip install -e . --force-reinstall

# 检查虚拟环境
python -c "import sys; print(sys.path)"
```

### 问题 4: API 调用失败

**错误信息:**
```
OpenAI API error: Authentication failed
```

**解决方案:**
1. 检查 API Key 是否正确设置
2. 验证 API Key 是否有效
3. 检查网络连接
4. 验证 API 端点是否可访问

### 问题 5: 端口占用

**错误信息:**
```
Error: [Errno 48] Address already in use
```

**解决方案:**
```bash
# 查找占用端口的进程
lsof -i :11211  # Linux/Mac
netstat -ano | findstr :11211  # Windows

# 杀死进程
kill -9 <PID>  # Linux/Mac
taskkill /F /PID <PID>  # Windows
```

---

## 📚 下一步

- 查看 [完整文档](../README_zh.md)
- 阅读 [改进计划](../IMPROVEMENT_PLAN.md)
- 了解 [API 文档](http://0.0.0.0:11211/docs)
- 贡献 [工具定义](../contribute_zh.md)

---

## 💡 提示

1. **使用虚拟环境** - 避免依赖冲突
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

2. **监控日志** - 查看运行状态
   ```bash
   tail -f logs/gtplanner.log
   ```

3. **测试连接** - 验证 API 配置
   ```bash
   python -c "from utils.openai_client import get_openai_client; print('OK')"
   ```

4. **性能优化** - 使用缓存
   - 配置向量服务缓存
   - 使用会话压缩
   - 启用智能压缩

---

## 🆘 获取帮助

- 📧 Issue: [GitHub Issues](https://github.com/OpenSQZ/GTPlanner/issues)
- 💬 Discussion: [GitHub Discussions](https://github.com/OpenSQZ/GTPlanner/discussions)
- 📖 文档: [完整文档](../README_zh.md)

