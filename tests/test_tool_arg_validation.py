import os
import sys


# 确保项目根目录在 Python 路径中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from agent.function_calling.agent_tools import validate_tool_arguments


def test_tool_recommend_normalization_clamp_max():
    res = validate_tool_arguments("tool_recommend", {"query": "RAG", "top_k": 100})
    assert res["valid"] is True
    assert res["errors"] == []
    assert res["normalized"]["top_k"] == 20  # 自动夹取到上限
    assert res["normalized"]["query"] == "RAG"
    # 默认 True
    assert res["normalized"]["use_llm_filter"] is True


def test_tool_recommend_normalization_clamp_min():
    res = validate_tool_arguments("tool_recommend", {"query": "RAG", "top_k": 0})
    assert res["valid"] is True
    assert res["normalized"]["top_k"] == 1  # 自动夹取到下限


def test_tool_recommend_invalid_tool_types():
    res = validate_tool_arguments(
        "tool_recommend",
        {"query": "RAG", "tool_types": ["INVALID"]},
    )
    assert res["valid"] is False
    assert isinstance(res["errors"], list) and len(res["errors"]) >= 1


def test_design_invalid_mode():
    res = validate_tool_arguments("design", {"design_mode": "fast"})
    assert res["valid"] is False


def test_design_valid_quick():
    res = validate_tool_arguments("design", {"design_mode": "quick"})
    assert res["valid"] is True
    assert res["normalized"]["design_mode"] == "quick"


def test_research_missing_keywords():
    res = validate_tool_arguments(
        "research",
        {"focus_areas": ["技术选型"], "project_context": "demo"},
    )
    assert res["valid"] is False


def test_research_missing_focus_areas():
    res = validate_tool_arguments(
        "research",
        {"keywords": ["RAG"]},
    )
    assert res["valid"] is False


def test_short_planning_missing_user_requirements():
    res = validate_tool_arguments("short_planning", {})
    assert res["valid"] is False


def test_short_planning_valid_default_stage():
    res = validate_tool_arguments(
        "short_planning",
        {"user_requirements": "设计一个用户管理系统"},
    )
    assert res["valid"] is True
    assert res["normalized"]["planning_stage"] == "initial"

