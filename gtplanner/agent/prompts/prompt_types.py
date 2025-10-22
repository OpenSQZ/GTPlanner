"""
提示词类型定义模块

定义所有提示词的类型枚举和分类，为统一管理提供基础。
"""

from enum import Enum
from typing import Dict, List


class PromptCategory(Enum):
    """提示词分类"""
    SYSTEM = "system"           # 系统级提示词
    AGENT = "agent"            # Agent专用提示词
    COMMON = "common"          # 通用提示词


class SystemPromptType(Enum):
    """系统级提示词类型"""
    ORCHESTRATOR_FUNCTION_CALLING = "orchestrator_function_calling"
    ERROR_HANDLING = "error_handling"
    VALIDATION = "validation"


class AgentPromptType(Enum):
    """Agent提示词类型"""
    # 短规划Agent
    SHORT_PLANNING_GENERATION = "short_planning_generation"

    # 研究Agent
    RESEARCH_ANALYSIS = "research_analysis"
    RESEARCH_SUMMARY = "research_summary"

    # 工具推荐Agent
    TOOL_RECOMMENDATION = "tool_recommendation"

    # 快速设计Agent
    QUICK_REQUIREMENTS_ANALYSIS = "quick_requirements_analysis"
    QUICK_DESIGN_OPTIMIZATION = "quick_design_optimization"

    # 深度设计Agent
    DEEP_REQUIREMENTS_ANALYSIS = "deep_requirements_analysis"
    NODE_IDENTIFICATION = "node_identification"
    FLOW_DESIGN = "flow_design"
    DATA_STRUCTURE_DESIGN = "data_structure_design"
    NODE_DESIGN = "node_design"
    DOCUMENT_GENERATION = "document_generation"


class CommonPromptType(Enum):
    """通用提示词类型"""
    CONTENT_ANALYSIS = "content_analysis"
    JSON_GENERATION = "json_generation"
    MARKDOWN_GENERATION = "markdown_generation"
    SUMMARY_GENERATION = "summary_generation"

    # 文本片段类型
    PREVIOUS_PLANNING_HEADER = "previous_planning_header"
    IMPROVEMENT_POINTS_HEADER = "improvement_points_header"
    IMPROVEMENT_INSTRUCTION = "improvement_instruction"
    TOOLS_HEADER = "tools_header"
    RESEARCH_HEADER = "research_header"
    NO_TOOLS_PLACEHOLDER = "no_tools_placeholder"
    NO_RESEARCH_PLACEHOLDER = "no_research_placeholder"
    BULLET_POINT = "bullet_point"

    # 工具相关文本片段
    UNKNOWN_TOOL = "unknown_tool"
    TOOL_FORMAT = "tool_format"

    # 研究相关文本片段
    RESEARCH_SUMMARY_PREFIX = "research_summary_prefix"
    KEY_FINDINGS_PREFIX = "key_findings_prefix"

    # 占位符文本片段
    NO_REQUIREMENTS_PLACEHOLDER = "no_requirements_placeholder"
    NO_PLANNING_PLACEHOLDER = "no_planning_placeholder"
    TOOL_BASED_PLANNING_PLACEHOLDER = "tool_based_planning_placeholder"
    DEFAULT_PROJECT_TITLE = "default_project_title"


class PromptTypeRegistry:
    """提示词类型注册表"""
    
    @staticmethod
    def get_all_prompt_types() -> Dict[PromptCategory, List[Enum]]:
        """获取所有提示词类型"""
        return {
            PromptCategory.SYSTEM: list(SystemPromptType),
            PromptCategory.AGENT: list(AgentPromptType),
            PromptCategory.COMMON: list(CommonPromptType)
        }
    
    @staticmethod
    def get_prompt_category(prompt_type: Enum) -> PromptCategory:
        """根据提示词类型获取分类"""
        if isinstance(prompt_type, SystemPromptType):
            return PromptCategory.SYSTEM
        elif isinstance(prompt_type, AgentPromptType):
            return PromptCategory.AGENT
        elif isinstance(prompt_type, CommonPromptType):
            return PromptCategory.COMMON
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    @staticmethod
    def get_prompt_path(prompt_type: Enum) -> str:
        """根据提示词类型获取文件路径"""
        category = PromptTypeRegistry.get_prompt_category(prompt_type)
        
        if category == PromptCategory.SYSTEM:
            if prompt_type == SystemPromptType.ORCHESTRATOR_FUNCTION_CALLING:
                return "system.orchestrator"
            elif prompt_type == SystemPromptType.ERROR_HANDLING:
                return "system.error_handling"
            elif prompt_type == SystemPromptType.VALIDATION:
                return "system.validation"
        
        elif category == PromptCategory.AGENT:
            # 根据Agent类型和节点分组
            if prompt_type.value == "short_planning_generation":
                return "agents.short_planning.short_planning_node"
            elif prompt_type.value == "research_analysis":
                return "agents.research.llm_analysis_node"
            elif prompt_type.value == "research_summary":
                return "agents.research.result_assembly_node"
            elif prompt_type.value == "tool_recommendation":
                return "agents.tool_recommend.node_tool_recommend"
            elif prompt_type.value == "quick_requirements_analysis":
                return "agents.quick_design.quick_requirements_analysis_node"
            elif prompt_type.value == "quick_design_optimization":
                return "agents.quick_design.quick_design_optimization_node"
            elif prompt_type.value == "deep_requirements_analysis":
                return "agents.deep_design.agent_requirements_analysis_node"
            elif prompt_type.value == "node_identification":
                return "agents.deep_design.node_identification_node"
            elif prompt_type.value == "flow_design":
                return "agents.deep_design.flow_design_node"
            elif prompt_type.value == "data_structure_design":
                return "agents.deep_design.data_structure_design_node"
            elif prompt_type.value == "node_design":
                return "agents.deep_design.node_design_node"
            elif prompt_type.value == "document_generation":
                return "agents.deep_design.document_generation_node"
        
        elif category == PromptCategory.COMMON:
            if prompt_type.value.endswith("_analysis"):
                return "common.analysis"
            elif prompt_type.value.endswith("_generation"):
                return "common.generation"
            elif prompt_type.value in [
                "previous_planning_header", "improvement_points_header",
                "improvement_instruction", "tools_header", "research_header",
                "no_tools_placeholder", "no_research_placeholder", "bullet_point",
                "unknown_tool", "tool_format", "research_summary_prefix", "key_findings_prefix",
                "no_requirements_placeholder", "no_planning_placeholder", "tool_based_planning_placeholder",
                "default_project_title"
            ]:
                return "common.text_fragments"
        
        raise ValueError(f"No path mapping found for prompt type: {prompt_type}")


# 便捷访问别名
class PromptTypes:
    """提示词类型便捷访问类"""
    System = SystemPromptType
    Agent = AgentPromptType
    Common = CommonPromptType
