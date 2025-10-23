"""
Design 子流程 - 统一的设计文档生成流程

这是一个简化的单节点流程，用于生成高层次的系统设计文档。
"""

from .flows.design_flow import DesignFlow
from .nodes.design_node import DesignNode

__all__ = [
    "DesignFlow",
    "DesignNode",
]

