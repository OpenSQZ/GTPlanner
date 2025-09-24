"""
Pydantic v2 argument models for Agent Function Calling tools.

These models provide strict validation and normalization for tool arguments,
replacing ad-hoc validation logic.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CShortPlanningArgs(BaseModel):
    """Arguments for the short_planning tool."""

    user_requirements: str = Field(..., description="原始用户需求描述")
    improvement_points: Optional[List[str]] = Field(
        default=None, description="改进点列表"
    )
    planning_stage: Literal["initial", "technical"] = Field(
        default="initial", description="规划阶段"
    )


class CToolRecommendArgs(BaseModel):
    """Arguments for the tool_recommend tool."""

    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量范围1-20")
    tool_types: Optional[List[Literal["PYTHON_PACKAGE", "APIS"]]] = Field(
        default=None, description="工具类型过滤"
    )
    use_llm_filter: bool = Field(default=True, description="是否使用LLM筛选")

    @field_validator("top_k", mode="before")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        # Double-guard to ensure constraint if top_k provided as lenient value
        if v < 1:
            return 1
        if v > 20:
            return 20
        return v


class CResearchArgs(BaseModel):
    """Arguments for the research tool."""

    keywords: List[str] = Field(..., min_length=1, description="关键词列表")
    focus_areas: List[str] = Field(..., min_length=1, description="调研关注点")
    project_context: Optional[str] = Field(default="", description="项目上下文")


class CDesignArgs(BaseModel):
    """Arguments for the design tool."""

    user_requirements: Optional[str] = Field(
        default=None, description="用户需求（可选，默认从short_planning中获取）"
    )
    design_mode: Literal["quick", "deep"] = Field(..., description="设计模式")


# Mapping from tool name to its argument model
TOOL_ARG_MODELS = {
    "short_planning": CShortPlanningArgs,
    "tool_recommend": CToolRecommendArgs,
    "research": CResearchArgs,
    "design": CDesignArgs,
}


