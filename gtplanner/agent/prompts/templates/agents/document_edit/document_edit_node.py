"""
Document Edit Node 提示词模板
对应 agent/subflows/document_edit/nodes/document_edit_node.py
"""


class AgentsDocumentEditDocumentEditNodeTemplates:
    """Document Edit 节点提示词模板类"""
    
    @staticmethod
    def get_document_edit_zh() -> str:
        """中文版本的文档编辑提示词"""
        return """你是一个文档编辑专家。你的任务是根据用户的修改需求，生成精确的 search/replace 操作。

# 当前文档内容

```markdown
{document_content}
```

# 用户的修改需求

{edit_instructions}

# 你的任务

请分析文档，生成精确的 search/replace 操作。每个操作包括：
1. **search**: 需要被替换的原文内容（必须从文档中精确复制，包含足够的上下文以确保唯一性）
2. **replace**: 替换后的新内容
3. **reason**: 修改原因说明（向用户解释）

# 输出格式

请以 JSON 格式输出，包含以下字段：
- `edits`: 编辑操作列表
- `summary`: 整体修改摘要

示例：
```json
{{
  "edits": [
    {{
      "search": "### 3.2 数据存储\\n\\n使用 PostgreSQL 作为主数据库。",
      "replace": "### 3.2 数据存储\\n\\n使用 PostgreSQL 作为主数据库，配合 Redis 作为缓存层。\\n\\n**缓存策略**：\\n- 热点数据缓存 TTL 设置为 1 小时\\n- 使用 LRU 淘汰策略",
      "reason": "根据用户需求添加 Redis 缓存层说明"
    }}
  ],
  "summary": "在数据存储章节添加了 Redis 缓存层的设计"
}}
```

# 重要规则

1. **精确匹配**：search 内容必须从原文档中精确复制，包括换行符、标点符号
2. **足够上下文**：确保 search 内容足够长，能在文档中唯一定位
3. **最少修改**：每个 search/replace 只修改一个局部，不要试图一次替换大段内容
4. **保持格式**：维持原文档的 Markdown 格式、缩进和结构

现在请开始分析文档并生成编辑操作。只输出 JSON，不要添加其他说明。
"""
    
    @staticmethod
    def get_document_edit_en() -> str:
        """英文版本的文档编辑提示词"""
        return """You are a document editing expert. Your task is to generate precise search/replace operations based on user's edit requirements.

# Current Document Content

```markdown
{document_content}
```

# User's Edit Requirements

{edit_instructions}

# Your Task

Analyze the document and generate precise search/replace operations. Each operation includes:
1. **search**: The original text to be replaced (must be copied exactly from the document, with enough context for unique identification)
2. **replace**: The new content after replacement
3. **reason**: Explanation of the change (explain to the user)

# Output Format

Output in JSON format with the following fields:
- `edits`: List of edit operations
- `summary`: Overall modification summary

Example:
```json
{{
  "edits": [
    {{
      "search": "### 3.2 Data Storage\\n\\nUsing PostgreSQL as the primary database.",
      "replace": "### 3.2 Data Storage\\n\\nUsing PostgreSQL as the primary database with Redis as the caching layer.\\n\\n**Caching Strategy**:\\n- Hot data cache TTL set to 1 hour\\n- Using LRU eviction policy",
      "reason": "Added Redis caching layer description as per user requirements"
    }}
  ],
  "summary": "Added Redis caching layer design in the data storage section"
}}
```

# Important Rules

1. **Exact Match**: Search content must be copied exactly from the original document, including line breaks and punctuation
2. **Sufficient Context**: Ensure search content is long enough for unique identification in the document
3. **Minimal Changes**: Each search/replace should only modify one local area, don't try to replace large sections at once
4. **Maintain Format**: Preserve the Markdown format, indentation, and structure of the original document

Now please begin analyzing the document and generating edit operations. Output only JSON, no additional explanations.
"""

