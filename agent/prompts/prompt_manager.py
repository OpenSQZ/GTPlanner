"""
统一提示词管理器

提供统一的多语言提示词加载、缓存和管理功能。
集成现有的language_detection.py，实现动态语言切换。
"""

import importlib
from typing import Dict, Optional, Any, Union
from functools import lru_cache

from utils.language_detection import LanguageDetector, SupportedLanguage
from .prompt_types import PromptTypeRegistry


class PromptManager:
    """统一提示词管理器"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self._template_cache: Dict[str, Dict[str, str]] = {}
        self._default_language = SupportedLanguage.CHINESE
    
    def get_prompt(self,
                   prompt_type: Union[str, Any],
                   language: Optional[Union[SupportedLanguage, str]] = None,
                   user_input: Optional[str] = None,
                   **kwargs) -> str:
        """
        获取指定类型和语言的提示词模板

        Args:
            prompt_type: 提示词类型（枚举或字符串）
            language: 目标语言，支持 SupportedLanguage 枚举或字符串（如 'zh', 'en'）
            user_input: 用户输入，用于语言检测（仅在language为None时使用）
            **kwargs: 模板参数，用于格式化提示词

        Returns:
            格式化后的提示词字符串
        """
        # 确定目标语言
        target_language = self._determine_language(language, user_input)
        
        # 获取提示词模板
        template = self._get_template(prompt_type, target_language)
        
        # 格式化模板
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing template parameter: {e}")
        
        return template
    
    def _determine_language(self,
                          explicit_language: Optional[Union[SupportedLanguage, str]],
                          user_input: Optional[str]) -> SupportedLanguage:
        """确定目标语言"""
        # 1. 显式指定的语言优先 - 直接返回，不需要检测
        if explicit_language:
            if isinstance(explicit_language, str):
                # 将字符串转换为 SupportedLanguage 枚举
                try:
                    return SupportedLanguage(explicit_language.lower())
                except ValueError:
                    # 如果字符串无效，使用默认语言
                    return self._default_language
            else:
                return explicit_language

        # 2. 从用户输入自动检测（仅在没有明确指定语言时）
        if user_input:
            detected = self.language_detector.detect_language(user_input)
            if detected != SupportedLanguage.ENGLISH:  # 如果检测到非英语
                return detected

        # 3. 使用默认语言
        return self._default_language
    
    @lru_cache(maxsize=128)
    def _get_template(self, prompt_type: Any, language: SupportedLanguage) -> str:
        """获取提示词模板（带缓存）"""
        # 转换为字符串键
        type_key = str(prompt_type.value) if hasattr(prompt_type, 'value') else str(prompt_type)
        cache_key = f"{type_key}_{language.value}"
        
        # 检查缓存
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # 加载模板
        template = self._load_template(prompt_type, language)
        
        # 缓存模板
        self._template_cache[cache_key] = template
        
        return template
    
    def _load_template(self, prompt_type: Any, language: SupportedLanguage) -> str:
        """从文件加载提示词模板"""
        try:
            # 获取模板路径
            template_path = PromptTypeRegistry.get_prompt_path(prompt_type)
            
            # 动态导入模板模块
            module_path = f"agent.prompts.templates.{template_path}"
            template_module = importlib.import_module(module_path)
            
            # 获取模板类
            class_name = self._get_template_class_name(template_path)
            template_class = getattr(template_module, class_name)
            
            # 获取语言特定的模板方法
            method_name = f"get_{prompt_type.value}_{language.value}"
            
            if hasattr(template_class, method_name):
                return getattr(template_class, method_name)()
            else:
                # 回退到中文模板
                fallback_method = f"get_{prompt_type.value}_zh"
                if hasattr(template_class, fallback_method):
                    return getattr(template_class, fallback_method)()
                else:
                    raise AttributeError(f"No template method found for {prompt_type}")
        
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load template for {prompt_type}: {e}")
    
    def _get_template_class_name(self, template_path: str) -> str:
        """根据模板路径生成类名"""
        parts = template_path.split('.')
        # 将下划线分隔的单词也转换为驼峰命名
        class_parts = []
        for part in parts:
            if '_' in part:
                # 处理下划线分隔的单词，如 short_planning_node -> ShortPlanningNode
                sub_parts = part.split('_')
                class_parts.extend([word.capitalize() for word in sub_parts])
            else:
                class_parts.append(part.capitalize())
        return ''.join(class_parts) + "Templates"
    
    def set_default_language(self, language: SupportedLanguage):
        """设置默认语言"""
        self._default_language = language
    
    def clear_cache(self):
        """清空模板缓存"""
        self._template_cache.clear()
        self._get_template.cache_clear()
    
    def preload_templates(self, prompt_types: list, languages: list):
        """预加载指定的模板"""
        for prompt_type in prompt_types:
            for language in languages:
                try:
                    self._get_template(prompt_type, language)
                except Exception as e:
                    print(f"Warning: Failed to preload {prompt_type} for {language}: {e}")


# 全局单例实例
_prompt_manager_instance = None

def get_prompt_manager() -> PromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance


# 便捷函数
def get_prompt(prompt_type: Any,
               language: Optional[Union[SupportedLanguage, str]] = None,
               user_input: Optional[str] = None,
               **kwargs) -> str:
    """
    便捷的提示词获取函数

    Args:
        prompt_type: 提示词类型
        language: 目标语言，支持 SupportedLanguage 枚举或字符串（如 'zh', 'en'）
        user_input: 用户输入，用于语言检测
        **kwargs: 模板参数
    """
    return get_prompt_manager().get_prompt(prompt_type, language, user_input, **kwargs)
