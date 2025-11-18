# 文档导出功能使用指南

## 功能概述

`export_document` 工具可以将已生成的设计文档导出为多种格式，方便用户在不同场景下使用。

## 支持的格式

- ✅ **MD**：Markdown 格式（直接保存）
- ✅ **HTML**：HTML 网页格式（带样式）
- ✅ **TXT**：纯文本格式（去除 Markdown 语法）
- ⏳ **PDF**：PDF 格式（暂未实现）
- ⏳ **DOCX**：Word 文档格式（暂未实现）

## 使用场景

### 1. 通过 CLI 交互式使用

启动 CLI 后，在对话中请求导出：

```
用户: 请将设计文档导出为 HTML 和 TXT 格式
```

LLM 会自动调用 `export_document` 工具完成导出。

### 2. 通过 Function Calling 直接调用

```python
from gtplanner.agent.function_calling.agent_tools import execute_agent_tool

# 准备参数
arguments = {
    "document_type": "design",
    "export_formats": ["html", "txt"],
    "output_dir": "output"
}

# 准备 shared 数据（包含已生成的文档）
shared = {
    "generated_documents": [
        {
            "type": "design",
            "filename": "design.md",
            "content": "# 设计文档内容..."
        }
    ]
}

# 执行导出
result = await execute_agent_tool("export_document", arguments, shared)
```

## 参数说明

### document_type
- **类型**：`string`
- **可选值**：`"design"` | `"database_design"` | `"all"`
- **说明**：要导出的文档类型
  - `"design"`：只导出设计文档
  - `"database_design"`：只导出数据库设计文档
  - `"all"`：导出所有文档

### export_formats
- **类型**：`array<string>`
- **可选值**：`["md", "html", "txt", "pdf", "docx"]`
- **说明**：要导出的格式列表，可以同时导出多种格式

### output_dir
- **类型**：`string`
- **默认值**：`"output"`
- **说明**：输出目录，导出的文件将保存到此目录

## 返回结果

成功时返回：

```json
{
    "success": true,
    "tool_name": "export_document",
    "saved_files": [
        {
            "document_type": "design",
            "format": "html",
            "filename": "design.html",
            "path": "output/design.html",
            "size": 6844
        },
        {
            "document_type": "design",
            "format": "txt",
            "filename": "design.txt",
            "path": "output/design.txt",
            "size": 2935
        }
    ],
    "total_exported": 2,
    "total_failed": 0
}
```

失败时返回：

```json
{
    "success": false,
    "error": "错误信息",
    "tool_name": "export_document"
}
```

## 示例

### 示例 1：导出单个文档为 HTML

```python
arguments = {
    "document_type": "design",
    "export_formats": ["html"]
}
```

### 示例 2：导出所有文档为多种格式

```python
arguments = {
    "document_type": "all",
    "export_formats": ["html", "txt", "md"]
}
```

### 示例 3：自定义输出目录

```python
arguments = {
    "document_type": "design",
    "export_formats": ["html"],
    "output_dir": "exports"
}
```

## 注意事项

1. **必须先有文档**：使用 `export_document` 前，必须先通过 `design` 或 `database_design` 工具生成文档
2. **PDF 和 DOCX 暂未实现**：目前只支持文本格式（MD、HTML、TXT）
3. **文件覆盖**：如果输出目录中已存在同名文件，会被覆盖
4. **编码**：所有文件使用 UTF-8 编码保存

## 技术实现

- **节点层**：`NodeExportDocument` (`gtplanner/agent/nodes/node_export.py`)
- **工具层**：`_execute_export_document` (`gtplanner/agent/function_calling/agent_tools.py`)
- **格式转换**：内置的 Markdown 到 HTML/TXT 转换器
- **文件保存**：使用 `FileGenerator` 工具类

## 测试

运行测试验证功能：

```bash
# 使用 uv 运行测试
uv run python -m pytest tests/test_export_conversion.py -v

# 运行简化测试脚本
uv run python tests/test_export_document_tool_simple.py
```

