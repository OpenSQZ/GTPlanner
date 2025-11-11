"""
GTPlanner 主控制流程模块

基于ReAct模式的智能主控制器，参考demo代码重构。
通过观察shared状态来智能决策，而不是复杂的思考-行动-观察循环。
"""

from .react_orchestrator_refactored import ReActOrchestratorRefactored

__all__ = [
    'ReActOrchestratorRefactored'
]
