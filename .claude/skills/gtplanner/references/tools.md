# GTPlanner 工具参数详解

本文档详细说明 GTPlanner 四个核心工具的参数、返回值和使用注意事项。

## API 入口

```python
from agent.function_calling.agent_tools import (
    execute_agent_tool,              # 执行工具
    get_agent_function_definitions   # 获取工具定义
)
```

---

## 1. short_planning - 短期规划

### 功能说明

定义和细化项目范围的核心工具，支持迭代优化。设计为根据用户反馈被重复调用，直到与用户就项目范围达成最终共识。

### 参数定义

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_requirements` | string | 是 | - | 用户的原始需求描述或新的需求补充 |
| `improvement_points` | array[string] | 否 | [] | 需要改进的点或新的需求列表 |
| `planning_stage` | string | 否 | "initial" | 规划阶段 |

### planning_stage 参数说明

| 值 | 说明 | 使用场景 |
|-----|------|----------|
| `initial` | 初始规划阶段 | 专注于需求分析和功能定义，不涉及技术选型 |
| `technical` | 技术规划阶段 | 在 tool_recommend 之后调用，整合推荐的技术栈 |

### 返回值

```python
{
    "success": True,
    "result": "规划结果文档（Markdown格式）",
    "tool_name": "short_planning"
}
```

### 状态影响

执行后会更新 `shared` 字典：

```python
shared["short_planning"] = "规划结果"
shared["user_requirements"] = "用户需求"
shared["planning_stage"] = "initial" | "technical"
```

### 使用示例

```python
# 首次调用 - 初始规划
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '开发一个在线商城系统',
        'planning_stage': 'initial'
    },
    shared
)

# 迭代优化 - 添加改进点
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '开发一个在线商城系统',
        'improvement_points': ['增加会员系统', '支持多种支付方式'],
        'planning_stage': 'initial'
    },
    shared
)

# 技术规划阶段 - 在 tool_recommend 之后
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '开发一个在线商城系统',
        'planning_stage': 'technical'
    },
    shared
)
```

---

## 2. tool_recommend - 工具推荐

### 功能说明

基于向量搜索为项目推荐平台支持的 API 或库。是 `research` 工具的强制前置步骤。

### 参数定义

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 查询文本，描述需要的工具功能 |
| `top_k` | integer | 否 | 5 | 返回的推荐工具数量 (1-20) |
| `tool_types` | array[string] | 否 | [] | 工具类型过滤 |
| `use_llm_filter` | boolean | 否 | true | 是否使用 LLM 筛选结果 |

### tool_types 可选值

| 值 | 说明 |
|-----|------|
| `PYTHON_PACKAGE` | Python 包 |
| `APIS` | API 服务 |

### 返回值

```python
{
    "success": True,
    "result": {
        "recommended_tools": [
            {
                "name": "工具名称",
                "description": "工具描述",
                "type": "PYTHON_PACKAGE" | "APIS",
                "score": 0.95
            }
        ],
        "total_found": 5,
        "search_time_ms": 120,
        "query_used": "查询文本",
        "index_name": "索引名称"
    },
    "tool_name": "tool_recommend"
}
```

### 状态影响

```python
shared["recommended_tools"] = [...]  # 推荐的工具列表
shared["query"] = "查询文本"
```

### 环境要求

需要配置向量搜索服务：

```bash
VECTOR_SERVICE_BASE_URL=your_vector_service_url
VECTOR_SERVICE_INDEX_NAME=document_gtplanner_tools
```

### 使用示例

```python
# 基本查询
result = await execute_agent_tool(
    'tool_recommend',
    {'query': '数据库ORM和用户认证'},
    shared
)

# 带过滤条件
result = await execute_agent_tool(
    'tool_recommend',
    {
        'query': 'Web框架和API开发',
        'top_k': 10,
        'tool_types': ['PYTHON_PACKAGE'],
        'use_llm_filter': True
    },
    shared
)
```

---

## 3. research - 技术调研

### 功能说明

使用 Jina Search 对推荐的技术栈进行深入可行性或实现方案调研。必须在 `tool_recommend` 成功调用之后使用。

### 前置条件

- 需要 `JINA_API_KEY` 环境变量
- 必须先调用 `tool_recommend`

### 参数定义

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keywords` | array[string] | 是 | - | 需要调研的关键词列表 |
| `focus_areas` | array[string] | 是 | - | 调研关注点列表 |
| `project_context` | string | 否 | "" | 项目背景信息 |

### focus_areas 建议值

- `技术选型` - 技术方案对比
- `性能优化` - 性能相关调研
- `最佳实践` - 行业最佳实践
- `架构设计` - 架构模式调研
- `安全性` - 安全相关考量
- `可扩展性` - 扩展性方案

### 返回值

```python
{
    "success": True,
    "result": {
        "keyword": "关键词",
        "findings": [
            {
                "source": "来源URL",
                "title": "文章标题",
                "summary": "摘要内容"
            }
        ]
    },
    "tool_name": "research",
    "keywords_processed": 3,
    "focus_areas": ["技术选型", "最佳实践"]
}
```

### 状态影响

```python
shared["research_findings"] = {...}  # 调研结果
shared["research_keywords"] = [...]  # 调研关键词
shared["focus_areas"] = [...]        # 关注点
```

### 使用示例

```python
result = await execute_agent_tool(
    'research',
    {
        'keywords': ['FastAPI', 'SQLAlchemy', 'Redis'],
        'focus_areas': ['技术选型', '性能优化', '最佳实践'],
        'project_context': '高并发电商后端系统'
    },
    shared
)
```

---

## 4. design - 架构设计

### 功能说明

综合所有前期成果，生成最终的系统架构方案和设计文档。调用此工具意味着整个规划流程的结束。

### 前置条件

- `shared` 字典中必须有 `short_planning` 结果

### 参数定义

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_requirements` | string | 是 | - | 最终确认的项目需求 |
| `design_mode` | string | 是 | - | 设计模式 |

### design_mode 参数说明

| 值 | 说明 | 适用场景 |
|-----|------|----------|
| `quick` | 快速设计 | 简单项目，流程简化，直接生成文档 |
| `deep` | 深度设计 | 复杂项目，包含完整需求分析和架构设计流程 |

### 返回值

```python
{
    "success": True,
    "message": "✅ 快速设计执行成功，设计文档已生成",
    "tool_name": "design",
    "design_mode": "快速设计" | "深度设计"
}
```

### 状态影响

```python
shared["agent_design_document"] = "完整的设计文档（Markdown格式）"
```

### 使用示例

```python
# 快速设计
result = await execute_agent_tool(
    'design',
    {
        'user_requirements': '用户需求描述...',
        'design_mode': 'quick'
    },
    shared
)

# 深度设计
result = await execute_agent_tool(
    'design',
    {
        'user_requirements': '用户需求描述...',
        'design_mode': 'deep'
    },
    shared
)
```

---

## 错误处理

所有工具在失败时返回统一格式：

```python
{
    "success": False,
    "error": "错误描述",
    "tool_name": "工具名称"
}
```

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `user_requirements is required` | 缺少必需参数 | 提供 user_requirements |
| `query is required` | 缺少查询文本 | 提供 query 参数 |
| `missing_jina_api_key` | 缺少 Jina API Key | 配置 JINA_API_KEY |
| `short_planning results are required` | 未先执行规划 | 先调用 short_planning |
| `design_mode must be 'quick' or 'deep'` | 无效的设计模式 | 使用有效值 |

---

## 工具获取

获取当前可用的工具定义：

```python
from agent.function_calling.agent_tools import get_agent_function_definitions

tools = get_agent_function_definitions()
for tool in tools:
    print(f"工具: {tool['function']['name']}")
    print(f"描述: {tool['function']['description'][:100]}...")
```

**注意**: `research` 工具只有在配置了 `JINA_API_KEY` 时才会出现在列表中。
