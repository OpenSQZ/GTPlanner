---
description: 初始化 GTPlanner 环境并验证配置
allowed-tools:
  - Bash
  - Read
---

# 初始化 GTPlanner

执行环境检查和配置验证。

## 检查步骤

### 1. 验证 Python 版本

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv run python --version
```

要求 Python >= 3.11

### 2. 检查依赖安装状态

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv sync --dry-run 2>&1 | head -20
```

如果有未安装的依赖，执行：

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv sync
```

### 3. 验证必需环境变量

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv run python -c "
import os
from dotenv import load_dotenv

load_dotenv()

required = ['LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL']
optional = ['JINA_API_KEY', 'VECTOR_SERVICE_BASE_URL', 'VECTOR_SERVICE_INDEX_NAME']

print('=== 必需配置 ===')
for var in required:
    value = os.getenv(var)
    status = '✅' if value and not value.startswith('your_') else '❌'
    print(f'{status} {var}: {\"已配置\" if status == \"✅\" else \"未配置或使用占位符\"}')

print()
print('=== 可选配置 ===')
for var in optional:
    value = os.getenv(var)
    status = '✅' if value and not value.startswith('your_') else '⚪'
    print(f'{status} {var}: {\"已配置\" if status == \"✅\" else \"未配置\"}')
"
```

### 4. 验证 GTPlanner 模块

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv run python -c "
from agent.function_calling.agent_tools import get_agent_function_definitions

tools = get_agent_function_definitions()
print('✅ GTPlanner 模块加载成功')
print()
print('可用工具:')
for tool in tools:
    name = tool['function']['name']
    desc = tool['function']['description'].split('\n')[0][:60]
    print(f'  - {name}: {desc}...')
"
```

### 5. 测试基本功能

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv run python -c "
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def test():
    shared = {}
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': '测试需求', 'planning_stage': 'initial'},
        shared
    )
    if result['success']:
        print('✅ short_planning 工具测试通过')
    else:
        print(f'❌ 测试失败: {result[\"error\"]}')
    return result['success']

success = asyncio.run(test())
exit(0 if success else 1)
"
```

## 初始化成功标志

当看到以下输出时，表示环境已正确配置：

```
✅ GTPlanner 模块加载成功
✅ short_planning 工具测试通过
```

## 常见问题

### 问题：LLM 配置错误

如果 LLM 相关环境变量未配置，请：

1. 复制 `.env.example` 为 `.env`
2. 填入正确的 LLM 配置

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
cp .env.example .env
# 然后编辑 .env 文件
```

### 问题：依赖安装失败

尝试清理并重新安装：

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
uv cache clean
uv sync
```

### 问题：模块导入失败

确保在项目根目录执行命令，并使用 `uv run`。
