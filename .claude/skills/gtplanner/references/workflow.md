# GTPlanner 工作流指南

本文档详细说明 GTPlanner 的标准工作流程、阶段划分和最佳实践。

## 工作流概览

GTPlanner 的完整工作流分为两个主要阶段：

```
┌─────────────────────────────────────────────────────────────────┐
│                      第一阶段：范围确认                           │
├─────────────────────────────────────────────────────────────────┤
│  short_planning (initial)  →  [用户反馈]  →  迭代优化           │
│                             ↓                                   │
│                      达成共识后进入下一阶段                       │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      第二阶段：技术实现                           │
├─────────────────────────────────────────────────────────────────┤
│  tool_recommend  →  short_planning (technical)  →  research*   │
│                                                       ↓         │
│                                                    design       │
└─────────────────────────────────────────────────────────────────┘
                                                    (* 可选)
```

---

## 第一阶段：范围确认

### 目标

与用户就项目范围达成共识，明确功能需求，不涉及技术选型。

### 工具调用

```python
# 初始需求分析
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '用户的原始需求',
        'planning_stage': 'initial'
    },
    shared
)
```

### 迭代优化

当用户对规划结果有修改意见时，使用 `improvement_points` 参数：

```python
# 根据用户反馈优化
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '用户的原始需求',
        'improvement_points': [
            '增加用户权限管理功能',
            '支持多语言切换',
            '添加数据导出功能'
        ],
        'planning_stage': 'initial'
    },
    shared
)
```

### 退出条件

- 用户确认规划结果满足需求
- 功能范围已明确定义
- 准备进入技术实现阶段

---

## 第二阶段：技术实现

### 步骤 1: 工具推荐

```python
# 基于确认的需求推荐技术栈
result = await execute_agent_tool(
    'tool_recommend',
    {
        'query': '基于规划结果描述技术需求',
        'top_k': 5,
        'tool_types': ['PYTHON_PACKAGE', 'APIS']
    },
    shared
)
```

### 步骤 2: 技术规划整合

```python
# 整合推荐的技术栈到规划中
result = await execute_agent_tool(
    'short_planning',
    {
        'user_requirements': '用户的原始需求',
        'planning_stage': 'technical'
    },
    shared
)
```

### 步骤 3: 深度调研（可选）

```python
# 对关键技术进行深入调研
result = await execute_agent_tool(
    'research',
    {
        'keywords': ['FastAPI', 'PostgreSQL', 'Redis'],
        'focus_areas': ['技术选型', '性能优化', '最佳实践'],
        'project_context': '项目背景描述'
    },
    shared
)
```

### 步骤 4: 生成设计文档

```python
# 生成最终设计文档
result = await execute_agent_tool(
    'design',
    {
        'user_requirements': '最终确认的需求',
        'design_mode': 'quick'  # 或 'deep'
    },
    shared
)
```

---

## 设计模式选择

### Quick 模式（快速设计）

**适用场景：**
- 简单项目或原型开发
- 时间紧迫的情况
- 需求明确且技术简单

**特点：**
- 流程简化
- 直接生成设计文档

**示例：**
```python
result = await execute_agent_tool(
    'design',
    {'user_requirements': '...', 'design_mode': 'quick'},
    shared
)
```

### Deep 模式（深度设计）

**适用场景：**
- 复杂企业级项目
- 需要详细架构规划
- 有充足时间进行设计

**特点：**
- 完整的需求分析流程
- 详细的架构设计
- 包含技术决策说明

**示例：**
```python
result = await execute_agent_tool(
    'design',
    {'user_requirements': '...', 'design_mode': 'deep'},
    shared
)
```

---

## 简化工作流

对于简单项目，可以跳过部分步骤：

### 最简流程

```python
shared = {}

# 1. 初始规划
await execute_agent_tool(
    'short_planning',
    {'user_requirements': '需求描述', 'planning_stage': 'initial'},
    shared
)

# 2. 快速设计
await execute_agent_tool(
    'design',
    {'user_requirements': '需求描述', 'design_mode': 'quick'},
    shared
)
```

### 适用条件

- 技术栈已确定，无需推荐
- 不需要深度技术调研
- 项目规模较小

---

## 状态流转

### shared 字典状态变化

```python
# 初始状态
shared = {}

# short_planning (initial) 执行后
shared = {
    "short_planning": "规划结果",
    "user_requirements": "用户需求",
    "planning_stage": "initial"
}

# tool_recommend 执行后
shared = {
    "short_planning": "规划结果",
    "user_requirements": "用户需求",
    "planning_stage": "initial",
    "recommended_tools": [...],
    "query": "查询文本"
}

# short_planning (technical) 执行后
shared = {
    "short_planning": "更新后的规划结果（含技术栈）",
    "user_requirements": "用户需求",
    "planning_stage": "technical",
    "recommended_tools": [...],
    "tool_recommend_status": "已获取工具推荐"
}

# research 执行后（可选）
shared = {
    ...
    "research_findings": {...}
}

# design 执行后
shared = {
    ...
    "agent_design_document": "完整设计文档"
}
```

---

## 错误恢复

### 工具执行失败时

1. 检查 `result["success"]` 是否为 `False`
2. 读取 `result["error"]` 获取错误信息
3. 根据错误类型决定处理方式

```python
result = await execute_agent_tool('short_planning', params, shared)

if not result['success']:
    error = result['error']
    if 'user_requirements is required' in error:
        # 缺少必需参数
        pass
    elif 'planning_stage must be' in error:
        # 参数值无效
        pass
    else:
        # 其他错误
        pass
```

### 从中间状态恢复

如果流程中断，可以从 `shared` 字典的当前状态继续：

```python
# 检查当前状态
if shared.get('short_planning') and not shared.get('recommended_tools'):
    # 已完成规划，未完成工具推荐
    await execute_agent_tool('tool_recommend', {...}, shared)
elif shared.get('recommended_tools') and not shared.get('agent_design_document'):
    # 已完成推荐，未完成设计
    await execute_agent_tool('design', {...}, shared)
```

---

## 最佳实践

### 1. 保持 shared 字典一致性

始终使用同一个 `shared` 字典传递给所有工具调用。

```python
# 正确做法
shared = {}
await execute_agent_tool('short_planning', params, shared)
await execute_agent_tool('tool_recommend', params, shared)  # 同一个 shared
await execute_agent_tool('design', params, shared)          # 同一个 shared

# 错误做法
await execute_agent_tool('short_planning', params, {})     # 不同的 shared
await execute_agent_tool('design', params, {})             # 丢失状态
```

### 2. 验证前置条件

在调用工具前检查必要的前置条件。

```python
# 调用 design 前检查
if not shared.get('short_planning'):
    raise ValueError("必须先执行 short_planning")
```

### 3. 处理空结果

`tool_recommend` 可能返回空结果，这是正常情况。

```python
result = await execute_agent_tool('tool_recommend', params, shared)
if result['success']:
    tools = result['result']['recommended_tools']
    if not tools:
        print("未找到匹配的工具，将使用默认技术栈")
```

### 4. 选择合适的设计模式

根据项目复杂度选择设计模式：

| 项目类型 | 推荐模式 |
|----------|----------|
| 小型工具/脚本 | quick |
| 简单 Web 应用 | quick |
| 中型项目 | quick 或 deep |
| 企业级应用 | deep |
| 复杂分布式系统 | deep |

### 5. 提供完整的项目背景

在调用 `research` 时，提供详细的 `project_context` 可以获得更精准的调研结果。

```python
await execute_agent_tool(
    'research',
    {
        'keywords': ['FastAPI', 'PostgreSQL'],
        'focus_areas': ['性能优化', '最佳实践'],
        'project_context': '''
        这是一个高并发电商系统的后端服务，
        预计日活用户 10 万，峰值 QPS 5000，
        需要支持秒杀活动和实时库存更新。
        '''
    },
    shared
)
```
