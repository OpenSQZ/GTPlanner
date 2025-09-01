"""
Research Agent 子流程包

完整的Research Agent实现，包含：
- 节点定义 (nodes/)
- 流程定义 (flows/)
- 工具类 (utils/)
- 测试文件 (test/)
"""


from .flows import ResearchFlow, create_keyword_research_subflow
from .nodes import LLMAnalysisNode, ResultAssemblyNode
from .utils import ResearchAggregator

__all__ = [
    'ResearchFlow',
    'create_keyword_research_subflow',
    'LLMAnalysisNode',
    'ResultAssemblyNode',
    'ResearchAggregator'
]
