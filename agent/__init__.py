"""
GTPlanner Agent 模块

GTPlanner (Graph Task Planner) 是一个基于ReAct模式的智能任务规划系统，
能够根据用户需求自动生成结构化的任务流程图和相关文档。

主要组件：
- context_types: 无状态数据类型定义
- pocketflow_factory: PocketFlow数据转换工厂
- nodes: 原子能力节点
- subflows: 专业Agent子流程
- flows: 主控制流程
- utils: 工具函数

使用示例：
```python
from agent import GTPlanner
from agent.context_types import AgentContext, create_user_message
from agent.pocketflow_factory import PocketFlowSharedFactory

# 创建GTPlanner实例
planner = GTPlanner()

# 创建上下文
context = AgentContext(
    session_id="test-session",
    dialogue_history=[create_user_message("我需要设计一个用户管理系统")],
    tool_execution_results={},
    session_metadata={}
)

# 处理用户需求
result = planner.process_user_request("我需要设计一个用户管理系统", context)
```
"""

from .context_types import (
    AgentContext, AgentResult, Message,
    MessageRole, create_user_message, create_assistant_message, create_tool_message
)
from .pocketflow_factory import PocketFlowSharedFactory, create_pocketflow_shared
# from .gtplanner import GTPlanner  # 暂时注释掉，文件过时需要重构


__all__ = [
    'AgentContext',
    'AgentResult',
    'Message',
    'ToolExecution',
    'MessageRole',
    'create_user_message',
    'create_assistant_message',
    'create_tool_message',
    'PocketFlowSharedFactory',
    'create_pocketflow_shared',
    # 'GTPlanner',  # 暂时注释掉
]

__version__ = "1.0.0"
