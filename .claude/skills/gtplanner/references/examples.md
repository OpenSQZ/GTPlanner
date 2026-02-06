# GTPlanner 使用示例

本文档提供 GTPlanner 的实际使用示例，涵盖不同场景和复杂度的项目。

## 示例 1：简单博客系统

### 场景

用户需要设计一个支持 Markdown 的个人博客系统。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def create_blog_prd():
    shared = {}
    user_requirements = """
    设计一个个人博客系统，包含以下功能：
    1. 支持 Markdown 编辑和预览
    2. 文章分类和标签管理
    3. 用户评论功能
    4. 简单的访问统计
    """

    # 步骤 1: 初始需求分析
    print("📋 正在分析需求...")
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'initial'},
        shared
    )
    print(f"初始规划: {'成功' if result['success'] else '失败'}")

    # 步骤 2: 工具推荐
    print("🔧 正在推荐技术栈...")
    result = await execute_agent_tool(
        'tool_recommend',
        {'query': 'Markdown编辑器、博客框架、评论系统', 'top_k': 5},
        shared
    )
    if result['success']:
        tools = result['result'].get('recommended_tools', [])
        print(f"推荐工具: {[t['name'] for t in tools]}")

    # 步骤 3: 技术规划整合
    print("📐 正在整合技术方案...")
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'technical'},
        shared
    )
    print(f"技术规划: {'成功' if result['success'] else '失败'}")

    # 步骤 4: 生成设计文档（快速模式）
    print("📝 正在生成设计文档...")
    result = await execute_agent_tool(
        'design',
        {'user_requirements': user_requirements, 'design_mode': 'quick'},
        shared
    )

    if result['success']:
        document = shared.get('agent_design_document', '')
        print("\n✅ 设计文档生成成功！")
        print("=" * 50)
        print(document[:500] + "...")  # 打印前 500 字符
    else:
        print(f"❌ 生成失败: {result['error']}")

    return shared

if __name__ == "__main__":
    asyncio.run(create_blog_prd())
```

---

## 示例 2：电商平台（深度设计）

### 场景

用户需要设计一个中型电商平台，包含完整的购物流程。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def create_ecommerce_prd():
    shared = {}
    user_requirements = """
    设计一个B2C电商平台，核心功能包括：

    用户端：
    - 用户注册、登录、个人中心
    - 商品浏览、搜索、收藏
    - 购物车管理
    - 订单创建、支付、查看
    - 评价和晒单

    商家端：
    - 商品管理（上架、下架、库存）
    - 订单管理
    - 数据统计

    技术要求：
    - 支持每日 10 万活跃用户
    - 需要支持促销活动
    - 移动端优先
    """

    # 阶段 1: 范围确认
    print("=" * 50)
    print("阶段 1: 范围确认")
    print("=" * 50)

    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'initial'},
        shared
    )
    print(f"初始规划完成: {result['success']}")

    # 模拟用户反馈 - 添加改进点
    improvement_points = [
        '需要支持微信和支付宝支付',
        '增加优惠券和积分系统',
        '添加客服在线咨询功能'
    ]

    result = await execute_agent_tool(
        'short_planning',
        {
            'user_requirements': user_requirements,
            'improvement_points': improvement_points,
            'planning_stage': 'initial'
        },
        shared
    )
    print(f"优化规划完成: {result['success']}")

    # 阶段 2: 技术实现
    print("\n" + "=" * 50)
    print("阶段 2: 技术实现")
    print("=" * 50)

    # 工具推荐
    result = await execute_agent_tool(
        'tool_recommend',
        {
            'query': '电商平台开发：支付接口、订单系统、库存管理、搜索引擎',
            'top_k': 10,
            'tool_types': ['PYTHON_PACKAGE', 'APIS']
        },
        shared
    )
    if result['success']:
        print(f"推荐工具数量: {result['result']['total_found']}")

    # 技术规划
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'technical'},
        shared
    )
    print(f"技术规划完成: {result['success']}")

    # 深度调研（可选，需要 JINA_API_KEY）
    print("\n尝试进行深度技术调研...")
    result = await execute_agent_tool(
        'research',
        {
            'keywords': ['微信支付', '秒杀系统', 'Redis缓存'],
            'focus_areas': ['技术选型', '性能优化', '高并发处理'],
            'project_context': '中型电商平台，预计日活 10 万用户'
        },
        shared
    )
    if result['success']:
        print("深度调研完成")
    else:
        print(f"调研跳过: {result.get('error', '未知原因')}")

    # 生成设计文档（深度模式）
    print("\n" + "=" * 50)
    print("阶段 3: 生成设计文档")
    print("=" * 50)

    result = await execute_agent_tool(
        'design',
        {'user_requirements': user_requirements, 'design_mode': 'deep'},
        shared
    )

    if result['success']:
        print("\n✅ 深度设计文档生成成功！")
        document = shared.get('agent_design_document', '')
        # 保存到文件
        with open('ecommerce_prd.md', 'w', encoding='utf-8') as f:
            f.write(document)
        print("📁 已保存到 ecommerce_prd.md")
    else:
        print(f"❌ 生成失败: {result['error']}")

    return shared

if __name__ == "__main__":
    asyncio.run(create_ecommerce_prd())
```

---

## 示例 3：API 服务设计

### 场景

用户需要设计一个 RESTful API 服务。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def create_api_service_prd():
    shared = {}
    user_requirements = """
    Design a RESTful API service for user authentication and authorization:

    Features:
    - User registration with email verification
    - Login with JWT tokens
    - Role-based access control (RBAC)
    - Password reset functionality
    - OAuth2 integration (Google, GitHub)
    - API rate limiting
    - Audit logging

    Technical requirements:
    - Response time < 100ms
    - Support 1000 concurrent users
    - High availability (99.9% uptime)
    """

    # 初始规划
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'initial'},
        shared
    )
    print(f"Initial planning: {'Success' if result['success'] else 'Failed'}")

    # 工具推荐
    result = await execute_agent_tool(
        'tool_recommend',
        {
            'query': 'JWT authentication, OAuth2, RBAC, rate limiting, API framework',
            'top_k': 8
        },
        shared
    )
    if result['success']:
        for tool in result['result'].get('recommended_tools', [])[:5]:
            print(f"  - {tool['name']}: {tool.get('description', '')[:50]}...")

    # 技术规划
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_requirements, 'planning_stage': 'technical'},
        shared
    )

    # 生成设计文档
    result = await execute_agent_tool(
        'design',
        {'user_requirements': user_requirements, 'design_mode': 'quick'},
        shared
    )

    if result['success']:
        print("\n✅ API Service PRD generated successfully!")
        return shared.get('agent_design_document', '')
    else:
        print(f"❌ Failed: {result['error']}")
        return None

if __name__ == "__main__":
    document = asyncio.run(create_api_service_prd())
    if document:
        print(document[:1000])
```

---

## 示例 4：迭代优化流程

### 场景

展示如何根据用户反馈迭代优化规划。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def iterative_planning_demo():
    shared = {}
    base_requirements = "设计一个任务管理应用"

    print("=== 第 1 轮：初始规划 ===\n")
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': base_requirements, 'planning_stage': 'initial'},
        shared
    )
    print("初始规划结果:")
    print(shared.get('short_planning', '')[:300])

    print("\n=== 第 2 轮：添加团队协作功能 ===\n")
    result = await execute_agent_tool(
        'short_planning',
        {
            'user_requirements': base_requirements,
            'improvement_points': ['支持团队协作', '添加任务分配功能'],
            'planning_stage': 'initial'
        },
        shared
    )
    print("优化后规划:")
    print(shared.get('short_planning', '')[:300])

    print("\n=== 第 3 轮：添加提醒功能 ===\n")
    result = await execute_agent_tool(
        'short_planning',
        {
            'user_requirements': base_requirements,
            'improvement_points': ['添加任务提醒和通知', '支持日历视图'],
            'planning_stage': 'initial'
        },
        shared
    )
    print("最终规划:")
    print(shared.get('short_planning', '')[:300])

    print("\n✅ 迭代优化完成，共进行了 3 轮规划")
    return shared

if __name__ == "__main__":
    asyncio.run(iterative_planning_demo())
```

---

## 示例 5：错误处理

### 场景

展示如何正确处理各种错误情况。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def error_handling_demo():
    """演示错误处理的最佳实践"""
    shared = {}

    # 错误 1: 缺少必需参数
    print("=== 测试 1: 缺少参数 ===")
    result = await execute_agent_tool(
        'short_planning',
        {'planning_stage': 'initial'},  # 缺少 user_requirements
        shared
    )
    if not result['success']:
        print(f"预期错误: {result['error']}")

    # 错误 2: 无效的参数值
    print("\n=== 测试 2: 无效参数 ===")
    result = await execute_agent_tool(
        'short_planning',
        {
            'user_requirements': '测试需求',
            'planning_stage': 'invalid_stage'  # 无效值
        },
        shared
    )
    if not result['success']:
        print(f"预期错误: {result['error']}")

    # 错误 3: 跳过前置步骤
    print("\n=== 测试 3: 跳过前置步骤 ===")
    empty_shared = {}  # 空的 shared，没有 short_planning 结果
    result = await execute_agent_tool(
        'design',
        {'user_requirements': '测试', 'design_mode': 'quick'},
        empty_shared
    )
    if not result['success']:
        print(f"预期错误: {result['error']}")

    # 正确流程
    print("\n=== 正确流程 ===")
    correct_shared = {}

    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': '设计一个简单的待办事项应用', 'planning_stage': 'initial'},
        correct_shared
    )
    if result['success']:
        print("✅ short_planning 成功")

        result = await execute_agent_tool(
            'design',
            {'user_requirements': '设计一个简单的待办事项应用', 'design_mode': 'quick'},
            correct_shared
        )
        if result['success']:
            print("✅ design 成功")
        else:
            print(f"❌ design 失败: {result['error']}")
    else:
        print(f"❌ short_planning 失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(error_handling_demo())
```

---

## 示例 6：多语言支持

### 场景

展示 GTPlanner 的多语言能力。

### 完整代码

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

async def multilingual_demo():
    """演示多语言支持"""

    languages = {
        'zh': "设计一个在线教育平台，支持视频课程和实时直播",
        'en': "Design an online education platform with video courses and live streaming",
        'ja': "ビデオコースとライブストリーミングをサポートするオンライン教育プラットフォームを設計してください"
    }

    for lang, requirements in languages.items():
        print(f"\n=== 语言: {lang.upper()} ===")
        shared = {}

        result = await execute_agent_tool(
            'short_planning',
            {'user_requirements': requirements, 'planning_stage': 'initial'},
            shared
        )

        if result['success']:
            output = shared.get('short_planning', '')
            # 显示前 200 字符
            print(f"输出预览: {output[:200]}...")
        else:
            print(f"失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(multilingual_demo())
```

---

## 示例 7：Claude Code 中的交互式使用

### 场景

在 Claude Code 环境中交互式使用 GTPlanner。

### 使用流程

1. **启动环境**

```bash
cd /path/to/GTPlanner
uv sync
```

2. **验证工具可用**

```bash
uv run python -c "
from agent.function_calling.agent_tools import get_agent_function_definitions
tools = get_agent_function_definitions()
print('可用工具:', [t['function']['name'] for t in tools])
"
```

3. **执行规划（Python 交互模式）**

```python
import asyncio
from agent.function_calling.agent_tools import execute_agent_tool

shared = {}

# 根据用户输入的需求执行
user_input = input("请输入您的项目需求: ")

async def run():
    result = await execute_agent_tool(
        'short_planning',
        {'user_requirements': user_input, 'planning_stage': 'initial'},
        shared
    )
    return result

result = asyncio.run(run())
print(shared.get('short_planning', ''))
```

4. **保存输出**

```python
document = shared.get('agent_design_document', '')
with open('output_prd.md', 'w', encoding='utf-8') as f:
    f.write(document)
print("文档已保存到 output_prd.md")
```

---

## 常见问题解答

### Q: 如何选择 quick 还是 deep 设计模式？

| 条件 | 推荐模式 |
|------|----------|
| 项目简单，功能明确 | quick |
| 时间紧迫 | quick |
| 复杂业务逻辑 | deep |
| 需要详细技术文档 | deep |
| 团队协作项目 | deep |

### Q: tool_recommend 返回空结果怎么办？

这是正常情况。可能的原因：
- 向量服务未配置
- 没有匹配的工具

**解决方案**：直接继续执行后续步骤，使用默认技术栈。

### Q: research 工具不可用怎么办？

需要配置 `JINA_API_KEY`。如果没有，可以跳过此步骤，直接执行 `design`。

### Q: 如何获取完整的设计文档？

设计文档存储在 `shared['agent_design_document']` 中：

```python
document = shared.get('agent_design_document', '')
```
