"""
GTPlanner CLI模块

基于SQLite和流式响应架构的现代化CLI界面：
- 现代化GTPlanner CLI (ModernGTPlannerCLI)
- 传统GTPlanner CLI (GTPlannerCLI) - 已弃用
"""

from .gtplanner_cli import ModernGTPlannerCLI

__all__ = [
    'ModernGTPlannerCLI'  # 现代化CLI，推荐使用
]
