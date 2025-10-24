"""
Agent Function Calling模块

提供将现有子Agent节点包装为OpenAI Function Calling工具的功能。
"""

from .agent_tools import (
    get_agent_function_definitions,
    execute_agent_tool,
    get_tool_by_name,
    validate_tool_arguments,
    call_tool_recommend,  # 已废弃，保留用于兼容性
    call_prefab_recommend,
    call_search_prefabs,
    call_research,
    call_design
)

__all__ = [
    "get_agent_function_definitions",
    "execute_agent_tool",
    "get_tool_by_name",
    "validate_tool_arguments",
    "call_tool_recommend",  # 已废弃，保留用于兼容性
    "call_prefab_recommend",
    "call_search_prefabs",
    "call_research",
    "call_design"
]
