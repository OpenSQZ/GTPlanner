"""
文本片段管理器

专门用于管理动态添加的文本片段，如分隔符、标题、提示语等。
提供便捷的多语言文本片段获取功能。
"""

from typing import Optional, List, Union
from utils.language_detection import SupportedLanguage
from .prompt_manager import get_prompt_manager
from .prompt_types import CommonPromptType


class TextManager:
    """文本片段管理器"""
    
    def __init__(self):
        self.prompt_manager = get_prompt_manager()
    
    def get_text(self,
                 text_type: CommonPromptType,
                 language: Optional[Union[SupportedLanguage, str]] = None,
                 user_input: Optional[str] = None,
                 **kwargs) -> str:
        """
        获取指定类型和语言的文本片段
        
        Args:
            text_type: 文本类型
            language: 目标语言，支持 SupportedLanguage 枚举或字符串（如 'zh', 'en'）
            user_input: 用户输入，用于语言检测
            **kwargs: 格式化参数
            
        Returns:
            格式化后的文本片段
        """
        return self.prompt_manager.get_prompt(text_type, language, user_input, **kwargs)
    
    def build_dynamic_content(self, 
                            user_requirements: str,
                            previous_planning: str = "",
                            improvement_points: List[str] = None,
                            recommended_tools: List[dict] = None,
                            research_findings: dict = None,
                            language: Optional[Union[SupportedLanguage, str]] = None) -> str:
        """
        构建动态内容，替代原来的硬编码字符串拼接
        
        Args:
            user_requirements: 用户需求
            previous_planning: 先前规划
            improvement_points: 改进点列表
            recommended_tools: 推荐工具列表
            research_findings: 研究发现
            language: 目标语言
            
        Returns:
            构建好的动态内容字符串
        """
        # 构建需求部分
        req_parts = [user_requirements]
        
        # 添加先前规划
        if previous_planning:
            header = self.get_text(CommonPromptType.PREVIOUS_PLANNING_HEADER, language)
            req_parts.append(header)
            req_parts.append(str(previous_planning))
        
        # 添加改进点
        if improvement_points:
            header = self.get_text(CommonPromptType.IMPROVEMENT_POINTS_HEADER, language)
            req_parts.append(header)
            
            # 构建改进点列表
            for point in improvement_points:
                bullet = self.get_text(CommonPromptType.BULLET_POINT, language, content=point)
                req_parts.append(bullet)
            
            # 添加改进指令
            instruction = self.get_text(CommonPromptType.IMPROVEMENT_INSTRUCTION, language)
            req_parts.append(instruction)
        
        return "\n".join(req_parts)
    
    def build_tools_content(self,
                          recommended_tools: List[dict] = None,
                          language: Optional[Union[SupportedLanguage, str]] = None) -> str:
        """
        构建工具清单内容
        
        Args:
            recommended_tools: 推荐工具列表
            language: 目标语言
            
        Returns:
            构建好的工具清单字符串
        """
        if not recommended_tools:
            return self.get_text(CommonPromptType.NO_TOOLS_PLACEHOLDER, language)
        
        tools_list = []
        for tool in recommended_tools:
            # 使用多语言文本片段获取未知工具名称
            unknown_tool_text = self.get_text(CommonPromptType.UNKNOWN_TOOL, language)
            tool_name = tool.get("name", tool.get("id", unknown_tool_text))
            tool_type = tool.get("type", "")
            tool_summary = tool.get("summary", tool.get("description", ""))

            # 使用多语言格式模板
            tool_line = self.get_text(
                CommonPromptType.TOOL_FORMAT,
                language,
                tool_name=tool_name,
                tool_type=tool_type,
                tool_summary=tool_summary
            )
            tools_list.append(tool_line)
        
        return "\n".join(tools_list)
    
    def build_research_content(self,
                             research_findings: dict = None,
                             language: Optional[Union[SupportedLanguage, str]] = None) -> str:
        """
        构建研究结果内容
        
        Args:
            research_findings: 研究发现
            language: 目标语言
            
        Returns:
            构建好的研究结果字符串
        """
        if not research_findings:
            return self.get_text(CommonPromptType.NO_RESEARCH_PLACEHOLDER, language)
        
        if "research_summary" in research_findings:
            # 使用多语言前缀
            prefix = self.get_text(CommonPromptType.RESEARCH_SUMMARY_PREFIX, language)
            return f"{prefix}{research_findings['research_summary']}"
        elif "key_findings" in research_findings:
            findings = research_findings["key_findings"]
            if isinstance(findings, list):
                # 使用多语言前缀
                prefix = self.get_text(CommonPromptType.KEY_FINDINGS_PREFIX, language)
                findings_text = f"{prefix}\n" + "\n".join(f"- {finding}" for finding in findings[:3])
                return findings_text
        
        return self.get_text(CommonPromptType.NO_RESEARCH_PLACEHOLDER, language)


# 全局单例实例
_text_manager_instance = None

def get_text_manager() -> TextManager:
    """获取全局文本管理器实例"""
    global _text_manager_instance
    if _text_manager_instance is None:
        _text_manager_instance = TextManager()
    return _text_manager_instance


# 便捷函数
def get_text(text_type: CommonPromptType,
             language: Optional[Union[SupportedLanguage, str]] = None,
             user_input: Optional[str] = None,
             **kwargs) -> str:
    """便捷的文本片段获取函数"""
    return get_text_manager().get_text(text_type, language, user_input, **kwargs)


def build_dynamic_content(user_requirements: str,
                        previous_planning: str = "",
                        improvement_points: List[str] = None,
                        recommended_tools: List[dict] = None,
                        research_findings: dict = None,
                        language: Optional[Union[SupportedLanguage, str]] = None) -> str:
    """便捷的动态内容构建函数"""
    return get_text_manager().build_dynamic_content(
        user_requirements, previous_planning, improvement_points,
        recommended_tools, research_findings, language
    )
