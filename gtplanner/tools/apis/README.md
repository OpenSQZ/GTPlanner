# OpenAI 兼容 API 工具配置说明

本目录包含了兼容 OpenAI API 格式的各种服务工具配置，支持多种供应商和模型提供商。

## 🔧 环境变量配置

这些工具支持通过环境变量进行灵活配置，以适应不同的服务提供商：

### 基础配置

```bash
# API 基础 URL（可选，默认为 OpenAI 官方地址）
export OPENAI_BASE_URL="https://api.openai.com/v1"

# API 密钥（必需）
export OPENAI_API_KEY="your-api-key-here"
```

### 常见供应商配置示例

#### 1. OpenAI 官方
```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="sk-your-openai-key"
```

#### 2. Azure OpenAI
```bash
export OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
export OPENAI_API_KEY="your-azure-key"
```

#### 3. 国内代理服务
```bash
export OPENAI_BASE_URL="https://api.chatanywhere.com.cn/v1"
export OPENAI_API_KEY="your-proxy-key"
```

#### 4. 本地部署服务
```bash
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="local-key"
```

#### 5. 其他兼容服务
```bash
# Anthropic Claude (通过代理)
export OPENAI_BASE_URL="https://api.anthropic-proxy.com/v1"
export OPENAI_API_KEY="your-claude-key"

# 智谱 GLM
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export OPENAI_API_KEY="your-glm-key"

# 阿里云通义千问
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_API_KEY="your-qwen-key"
```

## 📚 可用工具

### 1. 聊天完成 (Chat Completions)
- **文件**: `openai_chat.yml`
- **ID**: `openai-compatible.chat-completions`
- **功能**: 大语言模型对话和文本生成
- **支持模型**: GPT-4, GPT-3.5, Claude, Llama, 通义千问, GLM 等

### 2. 图像生成 (Image Generation)
- **文件**: `openai_dalle.yml`
- **ID**: `openai-compatible.dalle-image-generation`
- **功能**: 文本到图像生成
- **支持模型**: DALL-E 3, DALL-E 2, Midjourney API 等

### 3. 文本向量化 (Embeddings)
- **文件**: `openai_embeddings.yml`
- **ID**: `openai-compatible.embeddings`
- **功能**: 文本转向量，用于语义搜索
- **支持模型**: text-embedding-3, BGE, M3E 等

### 4. 音频处理 (Audio)
- **文件**: `openai_audio.yml`
- **ID**: `openai-compatible.audio`
- **功能**: 语音转文字、文字转语音
- **支持模型**: Whisper, TTS 等

## 🚀 使用示例

### Python 代码示例

```python
import os
import openai

# 配置客户端
openai.api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
openai.api_key = os.getenv("OPENAI_API_KEY")

# 聊天完成
response = openai.ChatCompletion.create(
    model="gpt-4",  # 或其他兼容模型
    messages=[
        {"role": "user", "content": "你好！"}
    ]
)

# 图像生成
image_response = openai.Image.create(
    model="dall-e-3",
    prompt="一只可爱的猫咪",
    size="1024x1024"
)

# 文本向量化
embedding_response = openai.Embedding.create(
    model="text-embedding-3-small",
    input="这是一段测试文本"
)
```

### cURL 示例

```bash
# 聊天完成
curl $OPENAI_BASE_URL/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 图像生成
curl $OPENAI_BASE_URL/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A cute cat",
    "size": "1024x1024"
  }'
```

## ⚠️ 注意事项

1. **模型兼容性**: 不同供应商支持的模型名称可能不同，请根据实际服务调整模型参数
2. **API 限制**: 各供应商的速率限制和使用限制可能不同
3. **功能支持**: 某些高级功能可能在不同供应商间有差异
4. **安全性**: 请妥善保管 API 密钥，不要在代码中硬编码

## 🔍 故障排除

### 常见问题

1. **连接失败**: 检查 `OPENAI_BASE_URL` 是否正确
2. **认证失败**: 检查 `OPENAI_API_KEY` 是否有效
3. **模型不存在**: 确认所使用的模型名称在目标服务中可用
4. **速率限制**: 降低请求频率或升级服务计划

### 调试技巧

```bash
# 测试连接
curl $OPENAI_BASE_URL/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 查看环境变量
echo "Base URL: $OPENAI_BASE_URL"
echo "API Key: ${OPENAI_API_KEY:0:10}..."
```

## 📖 更多信息

- 各工具的详细参数说明请查看对应的 `.yml` 文件
- 支持的模型列表请参考具体服务提供商的文档
- API 格式规范请参考 [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
