"""
Quick Requirements Analysis Node

使用基础需求分析节点重构，减少代码重复。
"""

from typing import Dict, Any

from agent.nodes.base_requirements_analysis_node import (
    BaseRequirementsAnalysisNode, AnalysisType, ProcessingMode
)
from agent.streaming import emit_design_document


class QuickRequirementsAnalysisNode(BaseRequirementsAnalysisNode):
    """快速需求分析节点 - 使用基础类重构"""

    def __init__(self):
        super().__init__(
            node_name="QuickRequirementsAnalysisNode",
            analysis_type=AnalysisType.QUICK,
            processing_mode=ProcessingMode.STANDARD,
            required_fields=["user_requirements"]
        )

    async def _prep_specific(self, shared: Dict[str, Any], prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """快速分析特定的准备逻辑"""
        # 快速分析不需要额外的准备逻辑
        return {}

    async def _process_analysis_result(self, analysis_result: str, prep_result: Dict[str, Any]) -> str:
        """处理快速分析结果"""
        # 快速分析直接返回LLM结果
        return analysis_result

    async def _post_specific(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ):
        """快速分析特定的后处理逻辑"""
        # 生成设计文档
        if exec_res.get("analysis_success"):
            await emit_design_document(
                shared,
                "quick_requirements_analysis.md",
                exec_res["analysis_result"]
            )


