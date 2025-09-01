"""
多语言提示词管理系统

提供统一的多语言提示词管理功能，支持动态语言检测和切换。
"""

from .prompt_manager import get_prompt_manager, get_prompt
from .prompt_types import PromptTypes, SystemPromptType, AgentPromptType, CommonPromptType

__all__ = [
    'get_prompt_manager',
    'get_prompt', 
    'PromptTypes',
    'SystemPromptType',
    'AgentPromptType', 
    'CommonPromptType'
]
