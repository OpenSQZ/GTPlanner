# 预制件函数查询工具文档

本文档介绍了 GTPlanner Agent 中新增的两个预制件函数查询工具，用于帮助 Agent 深入了解推荐的预制件内部有哪些函数，判断是否合适使用。

## 工具概览

| 工具名称 | 用途 | 调用时机 |
|---------|------|---------|
| `list_prefab_functions` | 查询预制件的所有函数列表 | 在 `prefab_recommend` 或 `search_prefabs` 后 |
| `get_function_details` | 查询单个函数的完整定义 | 在 `list_prefab_functions` 后 |

---

## 1. list_prefab_functions

### 功能描述

根据预制件 ID 查询该预制件的所有函数列表（仅包含函数名和描述）。

### 建议使用场景

当 `prefab_recommend` 或 `search_prefabs` 返回预制件推荐后，使用此工具查看预制件内部有哪些函数，判断是否符合需求。

### 参数

```json
{
  "prefab_id": "file-processing-prefab",  // 必需：预制件 ID
  "version": "0.1.5"                       // 可选：版本号（不指定则返回最新版本）
}
```

### 返回示例

```json
{
  "success": true,
  "result": {
    "prefab_id": "file-processing-prefab",
    "version": "0.1.5",
    "functions": [
      {
        "name": "parse_file",
        "description": "解析文件为 Markdown 格式的纯文本，支持 PDF、图片、文档等多种格式"
      }
    ],
    "total_functions": 1
  },
  "tool_name": "list_prefab_functions"
}
```

### 使用示例（Agent 工作流）

```python
# 步骤 1: Agent 推荐预制件
result = await execute_agent_tool("prefab_recommend", {
    "query": "我需要处理 PDF 文件，提取文本内容"
})
# 返回: [{"id": "file-processing-prefab", "version": "0.1.5", ...}]

# 步骤 2: Agent 查看预制件有哪些函数
result = await execute_agent_tool("list_prefab_functions", {
    "prefab_id": "file-processing-prefab"
})
# 返回: {"functions": [{"name": "parse_file", "description": "..."}]}

# 步骤 3: Agent 判断是否符合需求
# Agent 可以看到 parse_file 函数的描述，判断是否适合用户的需求
```

---

## 2. get_function_details

### 功能描述

根据预制件 ID 和函数名称获取该函数的完整定义（包括参数、返回值、文件定义等）。

### 建议使用场景

在调用 `list_prefab_functions` 后，针对感兴趣的函数查看其详细定义，了解如何调用。

### 参数

```json
{
  "prefab_id": "file-processing-prefab",  // 必需：预制件 ID
  "function_name": "parse_file",          // 必需：函数名称
  "version": "0.1.5"                       // 可选：版本号
}
```

### 返回示例

```json
{
  "success": true,
  "result": {
    "prefab_id": "file-processing-prefab",
    "version": "0.1.5",
    "function": {
      "name": "parse_file",
      "description": "解析文件为 Markdown 格式的纯文本，支持 PDF、图片、文档等多种格式",
      "parameters": [],
      "files": {
        "input": {
          "type": "array",
          "items": {"type": "InputFile"},
          "maxItems": 1,
          "minItems": 1,
          "required": true,
          "description": "要解析的文件（PDF、图片、Markdown 等）"
        },
        "output": {
          "type": "array",
          "items": {"type": "OutputFile"},
          "description": "解析后的 Markdown 文件"
        }
      },
      "returns": {
        "type": "object",
        "properties": {
          "success": {
            "type": "boolean",
            "description": "操作是否成功"
          },
          "content": {
            "type": "string",
            "optional": true,
            "description": "解析后的 Markdown 内容（成功时）"
          },
          "error": {
            "type": "string",
            "optional": true,
            "description": "错误信息（失败时）"
          }
        }
      }
    }
  },
  "tool_name": "get_function_details"
}
```

### 使用示例（Agent 工作流）

```python
# 步骤 1: 查看函数列表
result = await execute_agent_tool("list_prefab_functions", {
    "prefab_id": "file-processing-prefab"
})
# 返回: {"functions": [{"name": "parse_file", ...}]}

# 步骤 2: 查看感兴趣的函数的详细定义
result = await execute_agent_tool("get_function_details", {
    "prefab_id": "file-processing-prefab",
    "function_name": "parse_file"
})
# 返回: 完整的函数定义，包括参数、返回值、文件定义等

# 步骤 3: Agent 可以根据函数定义：
# - 了解函数需要什么输入（files.input）
# - 了解函数会返回什么（returns）
# - 判断这个函数是否适合当前用户需求
```

---

## 完整的 Agent 工作流示例

### 场景：用户想要处理 PDF 文件

```
用户输入: "我需要一个能处理 PDF 文件，提取其中文本内容的工具"

Agent 工作流:
1. 调用 prefab_recommend 推荐预制件
   └─ 返回: file-processing-prefab, document-parser-prefab

2. 调用 list_prefab_functions 查看第一个预制件的函数
   └─ 参数: {prefab_id: "file-processing-prefab"}
   └─ 返回: [{"name": "parse_file", "description": "解析文件为 Markdown..."}]

3. 调用 get_function_details 查看函数详情
   └─ 参数: {prefab_id: "file-processing-prefab", function_name: "parse_file"}
   └─ 返回: 完整的函数定义

4. Agent 分析:
   ✓ parse_file 函数支持 PDF 输入
   ✓ 返回 Markdown 格式的文本内容
   ✓ 符合用户需求

5. Agent 向用户推荐:
   "我找到了 file-processing-prefab 预制件，它提供 parse_file 函数，
    可以将 PDF 文件解析为 Markdown 格式的纯文本。这个预制件非常适合您的需求。"
```

---

## 配置

### 环境变量

需要配置 prefab-gateway 的 URL：

```bash
export GATEWAY_API_URL="http://localhost:8000"
```

### settings.toml

```toml
[prefab_gateway]
base_url = "http://localhost:8000"
```

---

## 错误处理

### 预制件不存在

```json
{
  "success": false,
  "error": "Prefab 'non-existent-prefab' not found",
  "tool_name": "list_prefab_functions"
}
```

### 函数不存在

```json
{
  "success": false,
  "error": "Function 'non_existent_function' not found in prefab file-processing-prefab@0.1.5",
  "tool_name": "get_function_details"
}
```

### Gateway 未配置

```json
{
  "success": false,
  "error": "Prefab gateway URL not configured",
  "tool_name": "list_prefab_functions"
}
```

---

## 优势

### 之前的问题

- Agent 只能推荐预制件，但不知道预制件内部有什么函数
- 无法判断推荐的预制件是否真的适合用户需求
- 用户需要自己去查看预制件文档

### 现在的改进

- ✅ Agent 可以主动查询预制件的函数列表
- ✅ Agent 可以了解每个函数的完整定义
- ✅ Agent 可以基于函数定义做出更准确的推荐
- ✅ Agent 可以向用户详细解释推荐的预制件能做什么

---

## 实现细节

### 文件位置

- **工具定义**: `/Users/ketd/code-ganyi/GTPlanner/gtplanner/agent/function_calling/agent_tools.py`
- **执行函数**: `_execute_list_prefab_functions()`, `_execute_get_function_details()`
- **配置函数**: `/Users/ketd/code-ganyi/GTPlanner/gtplanner/utils/config_manager.py` 的 `get_prefab_gateway_url()`

### API 端点

这两个工具调用的是 prefab-gateway 的公开接口（不需要鉴权）：

- `GET /v1/public/prefabs/{prefab_id}/functions` - List 接口
- `GET /v1/public/prefabs/{prefab_id}/functions/{function_name}` - Details 接口

### 技术栈

- **HTTP 客户端**: `httpx.AsyncClient`
- **超时设置**: 10 秒
- **错误处理**: HTTP 状态码 + 异常捕获

---

## 测试

### 手动测试

```python
import asyncio
from gtplanner.agent.function_calling.agent_tools import execute_agent_tool

async def test_prefab_functions():
    # 测试 list_prefab_functions
    result = await execute_agent_tool("list_prefab_functions", {
        "prefab_id": "file-processing-prefab"
    })
    print("Functions:", result)

    # 测试 get_function_details
    result = await execute_agent_tool("get_function_details", {
        "prefab_id": "file-processing-prefab",
        "function_name": "parse_file"
    })
    print("Details:", result)

asyncio.run(test_prefab_functions())
```

---

## 注意事项

1. **Gateway 可用性**: 确保 prefab-gateway 服务正在运行
2. **版本管理**: 不指定 version 参数时，返回最新部署的版本
3. **网络超时**: 设置了 10 秒超时，避免长时间等待
4. **错误提示**: 清晰的错误信息帮助 Agent 理解问题所在
