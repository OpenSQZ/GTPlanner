"""
Architecture Agent - 重构版本

专注于生成基于pocketflow的Agent设计文档。
不再关注数据校验，而是专注于Agent设计的核心内容。

主要功能：
- 基于需求和研究结果生成Agent设计文档
- 遵循pocketflow的Node/Flow设计模式
- 生成完整的Markdown格式设计文档
- 包含Flow设计、Node设计、数据结构等核心内容
"""

from .flows.deep_design_docs_flow import ArchitectureFlow
from .nodes.process_architecture_node import ProcessArchitectureNode

__all__ = [
    'ArchitectureFlow',
    'ProcessArchitectureNode'
]
