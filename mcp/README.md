# GTPlanner MCP 服务

GTPlanner 支持 Model Context Protocol (MCP)，可以直接在支持 MCP 的 AI 编程工具中使用。

---

## 📋 目录

- [什么是 MCP](#什么是-mcp)
- [快速开始](#快速开始)
- [客户端配置](#客户端配置)
- [可用工具](#可用工具)
- [使用示例](#使用示例)
- [故障排除](#故障排除)

---

## 🎯 什么是 MCP？

Model Context Protocol (MCP) 是一个标准协议，让 AI 助手能够调用外部工具和服务。

通过 MCP，你可以在 Cursor、Claude Desktop、Cherry Studio 等工具中直接使用 GTPlanner：
- 🚀 **无需切换**：在 IDE 中直接生成规划
- 🔄 **实时交互**：流式响应，查看生成过程
- 🧩 **智能推荐**：自动推荐合适的 Prefab
- 📝 **即刻可用**：生成的 PRD 直接用于编码

---

## 🚀 快速开始

### 环境要求

MCP 服务需要与主服务相同的环境变量配置。

### 安装依赖

```bash
cd mcp
uv sync
```

### 启动服务

```bash
uv run python mcp_service.py
```

服务默认运行在 `http://127.0.0.1:8001`

---

## ⚙️ 客户端配置

### Cursor 配置

在 Cursor 设置中添加 MCP 服务器：

**方式 1：直接连接运行中的服务**

```json
{
  "mcpServers": {
    "gtplanner": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

**方式 2：由客户端启动服务**

```json
{
  "mcpServers": {
    "gtplanner": {
      "command": "uv",
      "args": ["run", "python", "mcp_service.py"],
      "cwd": "/path/to/GTPlanner/mcp"
    }
  }
}
```

### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)：

```json
{
  "mcpServers": {
    "gtplanner": {
      "command": "uv",
      "args": ["run", "python", "/path/to/GTPlanner/mcp/mcp_service.py"],
      "env": {
        "LLM_API_KEY": "your-api-key",
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_MODEL": "gpt-4"
      }
    }
  }
}
```

### Cherry Studio 配置

在 Cherry Studio 的 MCP 设置中添加：

```json
{
  "name": "GTPlanner",
  "url": "http://127.0.0.1:8001/mcp"
}
```

---

## 🛠️ 可用工具

MCP 服务提供以下工具：

### 1. generate_flow

从需求生成规划流程（快速版本）。

**参数：**
- `requirements` (string, 必需): 需求描述
- `language` (string, 可选): 语言代码 (`en`, `zh`, `ja`, `es`, `fr`)，默认自动检测

**示例：**
```json
{
  "requirements": "设计一个智能邮件摘要助手，可以自动提取关键信息并生成简报",
  "language": "zh"
}
```

**返回：**
```json
{
  "flow": "规划流程内容...",
  "language_used": "zh"
}
```

### 2. generate_design_doc

生成详细的 PRD 文档（完整版本）。

**参数：**
- `requirements` (string, 必需): 需求描述
- `language` (string, 可选): 语言代码，默认自动检测

**示例：**
```json
{
  "requirements": "为PDF文档分析助手生成详细PRD，需要支持文本提取、摘要生成、智能问答",
  "language": "zh"
}
```

**返回：**
```json
{
  "document": "详细的PRD文档内容...",
  "metadata": {
    "language": "zh",
    "generated_at": "2024-10-23T12:00:00",
    "prefabs_recommended": ["prefab-1", "prefab-2"]
  }
}
```

---

## 💡 使用示例

### 在 Cursor 中使用

1. **配置 MCP 服务器**（参见上方）

2. **启动 GTPlanner MCP 服务**
   ```bash
   cd /path/to/GTPlanner/mcp
   uv run python mcp_service.py
   ```

3. **在 Cursor 中调用**

   打开 Cursor，在聊天中：
   ```
   @gtplanner 为一个视频分析助手生成规划
   ```
   
   或者使用命令面板：
   ```
   Cmd/Ctrl + Shift + P → "MCP: Call Tool" → 选择 gtplanner → generate_flow
   ```

### 在 Cherry Studio 中使用

1. 添加 MCP 服务器（参见客户端配置）

2. 在对话中使用：
   ```
   请使用 GTPlanner 为智能翻译助手生成详细的技术规划
   ```

3. Cherry Studio 会自动调用 `generate_design_doc` 工具

### 在 Claude Desktop 中使用

1. 配置 MCP 服务器

2. 重启 Claude Desktop

3. 在对话中：
   ```
   Use the gtplanner tool to generate a PRD for a document analysis assistant
   ```

---

## 🔍 使用场景

### 场景 1：快速规划

使用 `generate_flow` 快速获取项目结构：

```
需求：设计一个会议纪要生成助手
↓
GTPlanner MCP → generate_flow
↓
输出：
1. 音频录制和转文字
2. 关键要点提取
3. 行动项识别和分类
4. 参与者发言统计
5. 自动生成结构化纪要
```

### 场景 2：详细设计

使用 `generate_design_doc` 生成完整 PRD：

```
需求：智能代码审查助手
↓
GTPlanner MCP → generate_design_doc
↓
输出：
- 系统架构设计
- 功能模块详细说明
- 技术栈推荐
- Prefab 推荐
- 代码分析算法设计
- API 接口规范
- ...
```

### 场景 3：迭代优化

在编码过程中持续优化规划：

```
初始规划 → 编码 → 发现问题 → 调用 GTPlanner 调整规划 → 继续编码
```

---

## ⚙️ 高级配置

### 环境变量

MCP 服务需要以下环境变量（与主服务相同）：

```bash
# 必需
LLM_API_KEY="your-api-key"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"

# 可选
JINA_API_KEY="your-jina-key"  # 用于技术调研
LANGFUSE_SECRET_KEY="sk-lf-..."  # 用于追踪
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 端口配置

默认端口：`8001`

修改端口：

```python
# 编辑 mcp_service.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # 修改这里
```

### 日志配置

启用详细日志：

```bash
export LOG_LEVEL=DEBUG
uv run python mcp_service.py
```

---

## 🐛 故障排除

### 问题 1：服务无法启动

**症状：**
```
Error: No module named 'fastmcp'
```

**解决：**
```bash
cd mcp
uv sync  # 重新安装依赖
```

### 问题 2：客户端连接失败

**检查清单：**
1. ✅ MCP 服务是否正在运行？
   ```bash
   curl http://127.0.0.1:8001/health
   ```

2. ✅ 客户端配置中的路径是否正确？

3. ✅ 环境变量是否设置？
   ```bash
   echo $LLM_API_KEY
   ```

4. ✅ 防火墙是否阻止了端口？

### 问题 3：工具调用返回错误

**症状：**
```
Error: Missing required parameter 'requirements'
```

**解决：**
确保调用工具时提供了必需参数：

```json
{
  "requirements": "你的需求描述"  // 必需
}
```

### 问题 4：环境变量未生效

**症状：**
```
Error: LLM_API_KEY not configured
```

**解决：**

**方式 1：通过客户端配置传递**
```json
{
  "mcpServers": {
    "gtplanner": {
      "command": "uv",
      "args": ["run", "python", "mcp_service.py"],
      "cwd": "/path/to/GTPlanner/mcp",
      "env": {
        "LLM_API_KEY": "your-key",
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_MODEL": "gpt-4"
      }
    }
  }
}
```

**方式 2：使用 .env 文件**
```bash
cd /path/to/GTPlanner
cp .env.example .env
# 编辑 .env 设置环境变量
```

---

## 📊 性能优化

### 1. 使用本地缓存

MCP 服务会缓存 Prefab 索引，避免重复加载。

### 2. 调整超时时间

对于大型项目规划，可能需要更长的超时时间：

```python
# 编辑 mcp_service.py
# 增加 LLM 调用超时时间
```

### 3. 并发控制

默认支持多个客户端并发调用，每个请求独立处理。

---

## 🔗 相关文档

- [快速开始](../docs/zh/README.md#快速开始)
- [配置指南](../docs/zh/configuration.md)
- [CLI 文档](../gtplanner/agent/cli/README.md)
- [API 文档](../gtplanner/agent/api/README.md)

---

## 🌟 最佳实践

1. **保持服务运行**：将 MCP 服务作为后台服务运行
2. **使用版本控制**：将生成的 PRD 加入 Git 管理
3. **迭代优化**：根据实际编码过程持续调整规划
4. **配合 Prefab**：充分利用推荐的 Prefab 加速开发

---

<p align="center">
  有问题？<a href="https://github.com/OpenSQZ/GTPlanner/issues">提交 Issue</a>
</p>

