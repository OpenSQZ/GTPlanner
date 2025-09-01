"""
Quick Design Agent

智能设计文档生成Agent，根据配置自动选择设计模式：
- 快速设计模式：复用planning.py的简单直接逻辑
- 深度设计模式：使用循序渐进的6步架构设计流程

主要功能：
- 配置驱动的设计模式切换
- 基于ReAct模式的数据结构
- 复用现有的提示词模板
- 保持与现有接口的兼容性
"""

from .flows.quick_design_flow import QuickDesignFlow
from .nodes.quick_requirements_analysis_node import QuickRequirementsAnalysisNode
from .nodes.quick_design_optimization_node import QuickDesignOptimizationNode

__all__ = [
    'QuickDesignFlow',
    'QuickRequirementsAnalysisNode',
    'QuickDesignOptimizationNode'
]
