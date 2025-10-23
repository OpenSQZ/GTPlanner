# GTPlanner 导出功能使用指南

## 概述

GTPlanner 现在支持将规划结果导出为结构化的 Markdown 文件。导出功能支持多语言输出（中文、英文、日语、西班牙语、法语），可以保存完整对话历史或仅保存规划内容。

## 功能特性

### ✨ 核心特性

- **📄 Markdown 格式**: 导出为易读的 Markdown 文档
- **🌍 多语言支持**: 支持 5 种语言（中文、英文、日语、西班牙语、法语）
- **🎯 智能提取**: 自动提取规划相关内容
- **💬 完整记录**: 可选择包含完整对话历史
- **📂 自动命名**: 根据会话标题和时间戳自动生成文件名

### 📝 导出内容

导出的 Markdown 文件包含以下部分：

1. **标题**: 会话标题
2. **元数据**: 创建时间、会话ID、项目阶段、消息数量
3. **需求描述**: 第一条用户消息（初始需求）
4. **规划方案**: 自动提取的规划内容
5. **完整对话记录** (可选): 所有用户和助手的对话
6. **页脚**: 生成时间和工具信息

## 使用方法

### 1. CLI 命令行使用

#### 基本命令

```bash
# 保存当前会话的规划（默认保存为当前目录的 Plan.md）
/save

# 指定文件名（保存到当前目录）
/save my_planning.md

# 指定路径
/save outputs/project_plan.md

# 预览规划内容（不保存文件）
/preview
```

#### CLI 完整示例

```bash
# 启动 CLI
python gtplanner.py

# 输入需求
我想做一个在线教育平台

# ... 对话完成后 ...

# 预览规划内容
/preview

# 保存规划
/save

# 或指定路径保存
/save my_education_platform_plan.md
```

#### CLI 支持的语言

CLI 会根据启动时的 `--language` 参数选择导出语言：

```bash
# 中文界面和导出
python gtplanner.py --language zh

# 英文界面和导出
python gtplanner.py --language en

# 日文界面和导出
python gtplanner.py --language ja
```

### 2. API 接口使用

#### 导出端点

**POST** `/api/export/markdown`

导出会话规划到 Markdown 文件并返回内容。

**请求体**:
```json
{
  "session_id": "abc123...",
  "include_conversation": true,
  "language": "zh"
}
```

**参数说明**:
- `session_id` (必需): 会话ID
- `include_conversation` (可选): 是否包含完整对话，默认 `true`
- `language` (可选): 输出语言，支持 `zh`/`en`/`ja`/`es`/`fr`，默认 `zh`

**响应**:
```json
{
  "success": true,
  "file_path": "exports/项目规划_20251005_120000.md",
  "content": "# 项目规划\n\n...",
  "session_id": "abc123...",
  "timestamp": "2025-10-05T12:00:00"
}
```

#### 预览端点

**GET** `/api/export/preview/{session_id}`

预览规划内容（不保存文件）。

**查询参数**:
- `language`: 输出语言，默认 `zh`
- `max_length`: 最大预览长度，默认 `1000`

**响应**:
```json
{
  "success": true,
  "preview": "# 项目规划\n\n...",
  "session_id": "abc123...",
  "language": "zh",
  "timestamp": "2025-10-05T12:00:00"
}
```

#### API 使用示例

##### Python 示例

```python
import requests

# 导出规划
response = requests.post(
    "http://localhost:11211/api/export/markdown",
    json={
        "session_id": "your-session-id",
        "include_conversation": True,
        "language": "zh"
    }
)

result = response.json()
print(f"文件已保存到: {result['file_path']}")

# 预览规划
response = requests.get(
    f"http://localhost:11211/api/export/preview/your-session-id",
    params={"language": "en", "max_length": 500}
)

preview = response.json()
print(preview['preview'])
```

##### JavaScript/TypeScript 示例

```typescript
// 导出规划
const exportResponse = await fetch('http://localhost:11211/api/export/markdown', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'your-session-id',
    include_conversation: true,
    language: 'en'
  })
});

const result = await exportResponse.json();
console.log(`File saved to: ${result.file_path}`);

// 预览规划
const previewResponse = await fetch(
  `http://localhost:11211/api/export/preview/your-session-id?language=ja&max_length=500`
);

const preview = await previewResponse.json();
console.log(preview.preview);
```

##### cURL 示例

```bash
# 导出规划
curl -X POST http://localhost:11211/api/export/markdown \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "include_conversation": true,
    "language": "zh"
  }'

# 预览规划
curl "http://localhost:11211/api/export/preview/your-session-id?language=en&max_length=500"
```

### 3. Python 代码直接调用

```python
from agent.utils.export_planner import PlannerExporter
from agent.persistence.sqlite_session_manager import SQLiteSessionManager

# 创建导出器
session_manager = SQLiteSessionManager()
exporter = PlannerExporter(session_manager, language="zh")

# 导出当前会话
file_path = exporter.export_session_to_markdown(
    include_conversation=True,
    auto_filename=True
)
print(f"已保存到: {file_path}")

# 导出指定会话
file_path = exporter.export_session_to_markdown(
    session_id="specific-session-id",
    output_path="custom_path.md",
    include_conversation=False  # 仅导出规划内容
)

# 获取预览
preview = exporter.get_markdown_preview(
    session_id="specific-session-id",
    max_length=500
)
print(preview)
```

## 输出示例

### 中文输出示例

```markdown
# 在线教育平台规划

**创建时间**: 2025-10-05 12:00:00
**会话ID**: abc123...
**项目阶段**: design
**消息数量**: 6

---

## 📋 需求描述

我想做一个在线教育平台，需要有课程管理、学生管理和在线考试功能

## 🎯 规划方案

好的，我来为你设计一个在线教育平台的规划方案：

### 系统架构设计
...

## 💬 完整对话记录

### 👤 用户

我想做一个在线教育平台...

### 🤖 助手

好的，我来为你设计...

---

*此文档由 GTPlanner 自动生成于 2025-10-05 12:00:00*
```

### 英文输出示例

```markdown
# Online Education Platform Planning

**Created**: 2025-10-05 12:00:00
**Session ID**: abc123...
**Project Stage**: design
**Messages**: 6

---

## 📋 Requirements

I want to build an online education platform...

## 🎯 Planning

Sure, let me design a planning solution for you...

---

*Generated by GTPlanner at 2025-10-05 12:00:00*
```

## 文件存储

### 默认存储位置

导出的文件默认保存在**当前工作目录**。

### 文件命名规则

**默认文件名**: 如果不指定文件名，默认保存为 `Plan.md`

**命名逻辑**:
1. **不提供文件名**: 保存为 `Plan.md`（当前目录）
2. **只提供文件名**: 保存到 `<文件名>`（当前目录）
3. **提供相对路径**: 按相对路径保存（会自动创建目录）
4. **提供绝对路径**: 按绝对路径保存

**示例**:
```bash
# 默认 -> Plan.md
/save

# 指定文件名 -> my_plan.md
/save my_plan.md

# 相对路径 -> outputs/project.md
/save outputs/project.md

# 绝对路径 -> C:/Projects/plan.md (Windows)
/save C:/Projects/plan.md
```

### 自定义路径

```python
# CLI - 只提供文件名（保存到当前目录）
/save my_plan.md

# CLI - 提供路径
/save custom/path/my_plan.md        # 保存到 custom/path/my_plan.md

# Python API
exporter.export_session_to_markdown(
    output_path="custom/path/my_plan.md"
)
```

## 语言支持

### 支持的语言

| 语言代码 | 语言名称 | 使用示例 |
|---------|---------|---------|
| `zh` | 中文 | `language="zh"` |
| `en` | 英文 | `language="en"` |
| `ja` | 日语 | `language="ja"` |
| `es` | 西班牙语 | `language="es"` |
| `fr` | 法语 | `language="fr"` |

### 语言选择逻辑

1. **CLI**: 使用 `--language` 参数指定的语言
2. **API**: 使用请求中的 `language` 参数
3. **默认**: 如果未指定，默认使用中文 (`zh`)

## 高级功能

### 仅导出规划内容

如果只需要规划内容，不需要完整对话：

```python
# Python
exporter.export_planning_only(session_id="abc123")

# API
{
  "session_id": "abc123",
  "include_conversation": false
}
```

### 预览功能

在保存前预览内容：

```bash
# CLI
/preview

# Python
preview = exporter.get_markdown_preview(max_length=1000)
print(preview)
```

## 常见问题

### Q: 导出的文件在哪里？
A: 默认保存在当前工作目录，文件名为 `Plan.md`。如果指定了文件名，则保存为指定的文件名。

### Q: 如何更改导出语言？
A:
- CLI: 使用 `--language` 参数启动
- API: 在请求中指定 `language` 参数
- Python: 创建 `PlannerExporter` 时指定 `language` 参数

### Q: 可以只导出规划内容吗？
A: 可以，设置 `include_conversation=False` 参数。

### Q: 导出文件包含什么内容？
A: 包含会话元数据、需求描述、规划方案，以及可选的完整对话记录。

### Q: 如何查看会话ID？
A:
- CLI: 使用 `/sessions` 命令查看所有会话
- CLI: 使用 `/current` 命令查看当前会话信息

## 技术实现

### 核心组件

- **`PlannerExporter`**: 导出器核心类 (`agent/utils/export_planner.py`)
- **多语言模板**: 支持 5 种语言的 Markdown 模板
- **智能提取**: 自动识别和提取规划相关内容

### 数据流

```
会话数据 → PlannerExporter → Markdown 模板 → 文件输出
```

### 扩展性

添加新语言模板：

```python
TEMPLATES = {
    "new_lang": {
        "title": "# {title}\n\n",
        "metadata": "**Created**: {created_at}...",
        # ... 其他模板字段
    }
}
```

## 最佳实践

1. **及时保存**: 完成规划对话后及时导出，避免数据丢失
2. **语言一致**: 保持对话语言和导出语言一致，以获得最佳体验
3. **命名规范**: 使用描述性的文件名或让系统自动生成
4. **版本管理**: 对重要的规划文档进行版本控制

## 更新日志

### v1.0.0 (2025-10-05)
- ✨ 新增规划导出功能
- 🌍 支持 5 种语言输出
- 📝 CLI `/save` 和 `/preview` 命令
- 🔌 FastAPI 导出和预览端点
- 📚 完整的使用文档和示例
