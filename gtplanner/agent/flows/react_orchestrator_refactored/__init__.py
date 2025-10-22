"""
重构后的ReAct Orchestrator模块

提供模块化的ReAct主控制器实现，将原来的单一大类拆分为多个专门的组件。

主要组件：
- ReActOrchestratorNode: 主控制器节点
- ReActOrchestratorFlow: 主控制器流程
- TracedReActOrchestratorFlow: 带tracing的流程
- MessageBuilder: 消息构建器
- ToolExecutor: 工具执行器
- StateManager: 状态管理器
- StreamHandler: 流式处理器
- constants: 常量定义

优势：
1. 单一职责原则：每个组件只负责特定功能
2. 降低复杂度：将代码拆分为多个小文件
3. 提高可维护性：修改某个功能只需要修改对应组件
4. 增强可测试性：每个组件可以独立测试
5. 便于扩展：新功能可以通过新组件或扩展现有组件实现
6. 支持pocketflow_tracing：完整的执行轨迹追踪
"""

# 导入拆分后的组件
from .react_orchestrator_node import ReActOrchestratorNode
from .react_orchestrator_flow import ReActOrchestratorFlow, TracedReActOrchestratorFlow

# 向后兼容的别名
ReActOrchestratorRefactored = ReActOrchestratorFlow

# 导入其他组件

from .tool_executor import ToolExecutor


from . import constants

__all__ = [
    "ReActOrchestratorNode",
    "ReActOrchestratorFlow",
    "TracedReActOrchestratorFlow",
    "ReActOrchestratorRefactored",  # 向后兼容

    "ToolExecutor",


    "constants"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "GTPlanner Team"
__description__ = "Refactored ReAct Orchestrator with modular design"
