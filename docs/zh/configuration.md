# GTPlanner 配置指南

本文档详细说明 GTPlanner 的所有配置选项。

---

## 📋 目录

- [环境变量配置](#环境变量配置)
- [常见供应商配置](#常见供应商配置)
- [配置文件 (settings.toml)](#配置文件-settingstoml)
- [Langfuse 追踪配置](#langfuse-追踪配置)
- [常见问题](#常见问题)

---

## 🔑 环境变量配置

### 必需配置

创建 `.env` 文件（或设置环境变量）：

```bash
# LLM 核心配置（必需）
LLM_API_KEY="your-api-key-here"        # API 密钥
LLM_BASE_URL="https://api.openai.com/v1"  # API 基础 URL
LLM_MODEL="gpt-4"                       # 使用的模型名称
```

### 可选配置

```bash
# Jina AI 搜索服务（可选，用于技术调研功能）
JINA_API_KEY="your-jina-key"

# Langfuse 追踪（可选，用于执行过程追踪）
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 设置方式

**方式 1：使用 .env 文件（推荐）**

```bash
# 复制模板
cp .env.example .env

# 编辑 .env 文件
vim .env  # 或使用你喜欢的编辑器
```

**方式 2：直接设置环境变量**

```bash
# Linux/macOS
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4"

# Windows PowerShell
$env:LLM_API_KEY="your-api-key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4"
```

---

## 🌐 常见供应商配置

### OpenAI 官方

```bash
LLM_API_KEY="sk-proj-..."
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"  # 或 "gpt-4-turbo", "gpt-3.5-turbo"
```

### Azure OpenAI

```bash
LLM_API_KEY="your-azure-key"
LLM_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
LLM_MODEL="gpt-4"
```

**注意**：Azure OpenAI 的 URL 格式通常为：
```
https://{resource-name}.openai.azure.com/openai/deployments/{deployment-name}
```

### Anthropic Claude（通过代理）

如果使用兼容 OpenAI 格式的代理服务：

```bash
LLM_API_KEY="your-anthropic-api-key"
LLM_BASE_URL="https://your-proxy-service.com/v1"
LLM_MODEL="claude-3-opus-20240229"
```

### 国内代理服务

以常见的国内服务为例：

```bash
LLM_API_KEY="your-proxy-key"
LLM_BASE_URL="https://api.your-provider.com/v1"
LLM_MODEL="gpt-4"
```

### 本地部署模型

如果使用 Ollama、LocalAI 等本地服务：

```bash
LLM_API_KEY="not-required"  # 本地服务通常不需要
LLM_BASE_URL="http://localhost:11434/v1"  # Ollama 默认端口
LLM_MODEL="llama3"
```

---

## ⚙️ 配置文件 (settings.toml)

`settings.toml` 用于配置更高级的选项。

### 基础配置

```toml
[default]
# 默认语言
language = "zh"  # 可选: en, zh, ja, es, fr

# 日志级别
log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

### 多语言配置

```toml
[default.multilingual]
default_language = "zh"
auto_detect = true
fallback_enabled = true
supported_languages = ["en", "zh", "es", "fr", "ja"]
```

### 向量服务配置（Prefab 推荐系统）

```toml
[default.vector_service]
# 向量嵌入模型
embedding_model = "text-embedding-ada-002"

# 向量数据库配置
vector_db_path = "workspace/vector_index"

# Prefab 索引预加载
preload_index = true
```

### 执行追踪配置

```toml
[default.tracing]
# 是否启用追踪
enabled = true

# Langfuse 配置（优先使用环境变量）
# langfuse_public_key = "pk-lf-..."
# langfuse_secret_key = "sk-lf-..."
# langfuse_host = "https://cloud.langfuse.com"
```

**注意**：敏感信息（如 API Key）建议使用环境变量，不要直接写在 `settings.toml` 中。

---

## 📊 Langfuse 追踪配置

Langfuse 用于追踪 GTPlanner 的执行过程，帮助分析性能和调试问题。

### 为什么使用 Langfuse？

- 📈 **性能分析**：查看每个步骤的耗时
- 🔍 **问题调试**：追踪执行流程，定位问题
- 💰 **成本监控**：统计 Token 使用量
- 📊 **质量评估**：分析生成质量

### 快速配置

**方式 1：使用配置脚本（推荐）**

```bash
bash configure_langfuse.sh
```

脚本会引导你：
1. 创建 Langfuse 账号
2. 获取 API 密钥
3. 自动配置环境变量

**方式 2：手动配置**

1. 访问 [Langfuse Cloud](https://cloud.langfuse.com) 注册账号

2. 创建新项目，获取 API 密钥：
   - Public Key: `pk-lf-...`
   - Secret Key: `sk-lf-...`

3. 在 `.env` 文件中添加：
   ```bash
   LANGFUSE_PUBLIC_KEY="pk-lf-your-public-key"
   LANGFUSE_SECRET_KEY="sk-lf-your-secret-key"
   LANGFUSE_HOST="https://cloud.langfuse.com"
   ```

### 禁用 Langfuse

如果暂时不需要追踪功能：

```bash
# 方式 1: 不设置 Langfuse 环境变量（推荐）
# 系统会自动跳过 tracing

# 方式 2: 在 settings.toml 中禁用
[default.tracing]
enabled = false
```

---

## ❓ 常见问题

### Q1: API Key 配置后不生效？

**检查清单：**
1. 确认 `.env` 文件在项目根目录
2. 确认环境变量名称正确（`LLM_API_KEY` 而非 `OPENAI_API_KEY`）
3. 重启服务（修改 `.env` 后需要重启）
4. 检查是否有空格或特殊字符

### Q2: 支持哪些模型？

GTPlanner 支持任何兼容 OpenAI API 格式的模型：
- OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- Azure OpenAI: 任何部署的模型
- Anthropic: claude-3-opus, claude-3-sonnet（通过代理）
- 本地模型: 通过 Ollama、LocalAI 等兼容服务

### Q3: 如何使用自己的 Base URL？

设置 `LLM_BASE_URL` 为你的服务地址：

```bash
# 确保 URL 以 /v1 结尾
LLM_BASE_URL="https://your-service.com/v1"
```

### Q4: Jina API Key 是必需的吗？

**不是必需的**。Jina API 仅用于技术调研功能：
- 不设置：技术调研功能会被跳过
- 设置后：可以使用网络搜索进行技术调研

获取 Jina API Key: [https://jina.ai/](https://jina.ai/)

### Q5: 配置优先级是什么？

GTPlanner 配置优先级（从高到低）：

1. **环境变量** (最高优先级)
2. `.env` 文件
3. `settings.toml`
4. 默认值

建议：
- API Key 等敏感信息 → 使用环境变量或 `.env`
- 应用配置（语言、日志级别等）→ 使用 `settings.toml`

### Q6: 如何验证配置是否正确？

运行快速测试：

```bash
# 测试 LLM 连接
python -c "from gtplanner.utils.openai_client import get_openai_client; client = get_openai_client(); print('✅ LLM 配置正常')"

# 测试完整服务启动
uv run python fastapi_main.py
# 如果成功启动，说明配置正确
```

---

## 🔗 相关文档

- [快速开始](README.md#快速开始) - 基础配置和使用
- [CLI 文档](../../gtplanner/agent/cli/README.md) - CLI 特定配置
- [API 文档](../../gtplanner/agent/api/README.md) - API 服务配置
- [MCP 文档](../../mcp/README.md) - MCP 服务配置

---

<p align="center">
  有问题？查看 <a href="https://github.com/OpenSQZ/GTPlanner/issues">GitHub Issues</a> 或提交新问题
</p>

