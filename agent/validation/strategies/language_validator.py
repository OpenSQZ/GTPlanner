"""
多语言验证策略

基于策略模式的多语言验证实现，提供：
- 语言检测和验证
- 支持语言列表检查
- 语言一致性验证
- 自动语言回退
- 集成现有MultilingualManager
"""

import re
from typing import Dict, Any, List, Optional, Set
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖

# 尝试导入现有的多语言管理器
try:
    from utils.multilingual_utils import MultilingualManager
    from utils.language_detection import get_supported_languages, is_supported_language, detect_language
    MULTILINGUAL_AVAILABLE = True
except ImportError:
    MULTILINGUAL_AVAILABLE = False


class LanguageValidationStrategy(IValidationStrategy):
    """多语言验证策略 - 检查语言支持和一致性"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.supported_languages = config.get("supported_languages", ["en", "zh", "es", "fr", "ja"])
        self.auto_detect_language = config.get("auto_detect_language", True)
        self.fallback_to_default = config.get("fallback_to_default", True)
        self.validate_language_consistency = config.get("validate_language_consistency", False)
        
        # 初始化多语言管理器
        if MULTILINGUAL_AVAILABLE:
            try:
                self.multilingual_manager = MultilingualManager()
                self.available_languages = get_supported_languages()
            except Exception:
                self.multilingual_manager = None
                self.available_languages = ["en", "zh", "es", "fr", "ja"]
        else:
            self.multilingual_manager = None
            self.available_languages = ["en", "zh", "es", "fr", "ja"]
        
        # 语言检测模式
        self.language_patterns = self._compile_language_patterns()
    
    def _compile_language_patterns(self) -> Dict[str, re.Pattern]:
        """编译语言检测模式"""
        patterns = {
            "zh": re.compile(r'[\u4e00-\u9fff]+'),  # 中文字符
            "ja": re.compile(r'[\u3040-\u309f\u30a0-\u30ff]+'),  # 日文字符
            "ko": re.compile(r'[\uac00-\ud7af]+'),  # 韩文字符
            "ar": re.compile(r'[\u0600-\u06ff]+'),  # 阿拉伯文字符
            "ru": re.compile(r'[\u0400-\u04ff]+'),  # 俄文字符
        }
        return patterns
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行多语言验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        if not isinstance(data, dict):
            return result
        
        # 验证会话元数据中的语言设置
        await self._validate_session_language(data, result)
        
        # 验证对话内容的语言
        if "dialogue_history" in data:
            await self._validate_dialogue_languages(data["dialogue_history"], result)
        
        return result
    
    async def _validate_session_language(self, data: dict, result: ValidationResult) -> None:
        """验证会话语言设置"""
        session_metadata = data.get("session_metadata", {})
        
        if isinstance(session_metadata, dict) and "language" in session_metadata:
            specified_language = session_metadata["language"]
            
            # 检查语言代码格式
            if not isinstance(specified_language, str):
                error = ValidationError.create_format_error(
                    field="session_metadata.language",
                    expected_type="字符串",
                    actual_value=type(specified_language).__name__,
                    validator="language"
                )
                result.add_error(error)
                return
            
            # 标准化语言代码
            normalized_lang = specified_language.lower().strip()
            
            # 检查语言代码长度
            if len(normalized_lang) < 2 or len(normalized_lang) > 5:
                error = ValidationError(
                    code="INVALID_LANGUAGE_CODE_FORMAT",
                    message=f"语言代码格式无效：'{specified_language}'",
                    field="session_metadata.language",
                    value=specified_language,
                    validator="language",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion="请使用2-5字符的语言代码，如：'en', 'zh', 'es', 'fr', 'ja'"
                )
                result.add_error(error)
                return
            
            # 检查是否为支持的语言
            if MULTILINGUAL_AVAILABLE:
                if not is_supported_language(normalized_lang):
                    error = ValidationError(
                        code="UNSUPPORTED_LANGUAGE",
                        message=f"不支持的语言：'{specified_language}'",
                        field="session_metadata.language",
                        value=specified_language,
                        validator="language",
                        severity=ValidationSeverity.MEDIUM,
                        suggestion=f"请使用支持的语言：{', '.join(self.available_languages)}",
                        metadata={"available_languages": self.available_languages}
                    )
                    if self.fallback_to_default:
                        result.add_warning(error)  # 如果支持回退，则作为警告
                    else:
                        result.add_error(error)    # 否则作为错误
            else:
                # 如果多语言管理器不可用，使用配置的支持语言列表
                if normalized_lang not in self.supported_languages:
                    error = ValidationError(
                        code="UNSUPPORTED_LANGUAGE",
                        message=f"不支持的语言：'{specified_language}'",
                        field="session_metadata.language",
                        value=specified_language,
                        validator="language",
                        severity=ValidationSeverity.MEDIUM,
                        suggestion=f"请使用支持的语言：{', '.join(self.supported_languages)}",
                        metadata={"supported_languages": self.supported_languages}
                    )
                    if self.fallback_to_default:
                        result.add_warning(error)
                    else:
                        result.add_error(error)
    
    async def _validate_dialogue_languages(self, dialogue_history: Any, result: ValidationResult) -> None:
        """验证对话内容的语言"""
        if not isinstance(dialogue_history, list) or not self.auto_detect_language:
            return
        
        detected_languages = set()
        
        for i, message in enumerate(dialogue_history):
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                if isinstance(content, str) and len(content.strip()) > 10:  # 只检测足够长的内容
                    detected_lang = await self._detect_content_language(content)
                    if detected_lang:
                        detected_languages.add(detected_lang)
        
        # 检查语言一致性
        if self.validate_language_consistency and len(detected_languages) > 2:
            error = ValidationError(
                code="INCONSISTENT_LANGUAGES",
                message=f"检测到多种语言混用：{', '.join(detected_languages)}",
                field="dialogue_history",
                validator="language",
                severity=ValidationSeverity.LOW,
                suggestion="建议在同一会话中保持语言一致性",
                metadata={"detected_languages": list(detected_languages)}
            )
            result.add_warning(error)
        
        # 检查是否包含不支持的语言
        unsupported_languages = detected_languages - set(self.supported_languages)
        if unsupported_languages:
            error = ValidationError(
                code="UNSUPPORTED_LANGUAGE_DETECTED",
                message=f"检测到不支持的语言：{', '.join(unsupported_languages)}",
                field="dialogue_history",
                validator="language",
                severity=ValidationSeverity.LOW,
                suggestion=f"建议使用支持的语言：{', '.join(self.supported_languages)}",
                metadata={"unsupported_languages": list(unsupported_languages)}
            )
            result.add_warning(error)
    
    async def _detect_content_language(self, content: str) -> Optional[str]:
        """检测内容语言"""
        if MULTILINGUAL_AVAILABLE:
            try:
                return detect_language(content)
            except Exception:
                pass
        
        # 简单的基于正则的语言检测
        for lang, pattern in self.language_patterns.items():
            if pattern.search(content):
                return lang
        
        # 如果包含主要是ASCII字符，假设为英文
        ascii_chars = sum(1 for c in content if ord(c) < 128)
        if ascii_chars / len(content) > 0.8:
            return "en"
        
        return None
    
    def get_strategy_name(self) -> str:
        return "language"


# class LanguageValidator(BaseValidator):  # 暂时注释避免dynaconf依赖
    """多语言验证器 - 基于BaseValidator的完整实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.strategy = LanguageValidationStrategy(config)
    
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        """执行多语言验证逻辑"""
        # 将检测到的语言添加到上下文中
        result = await self.strategy.execute(context.request_data, context.validation_rules)
        
        # 如果启用了语言检测，尝试检测主要语言
        if self.strategy.auto_detect_language and isinstance(context.request_data, dict):
            dialogue_history = context.request_data.get("dialogue_history", [])
            if isinstance(dialogue_history, list) and dialogue_history:
                # 检测最后一条用户消息的语言
                for message in reversed(dialogue_history):
                    if (isinstance(message, dict) and 
                        message.get("role") == "user" and 
                        "content" in message):
                        content = message["content"]
                        if isinstance(content, str) and len(content.strip()) > 5:
                            detected_lang = await self.strategy._detect_content_language(content)
                            if detected_lang:
                                context.detected_language = detected_lang
                                break
        
        return result
    
    def get_validator_name(self) -> str:
        return "language"
    
    def get_priority(self) -> ValidatorPriority:
        return ValidatorPriority.LOW  # 语言验证优先级较低
    
    def can_cache_result(self) -> bool:
        # 语言验证结果可以缓存
        return self.config.get("enable_cache", True)
    
    def get_cache_key(self, context: ValidationContext) -> Optional[str]:
        """生成语言验证的缓存键"""
        if not self.can_cache_result():
            return None
        
        # 基于语言设置和内容语言生成缓存键
        session_lang = None
        content_lang_hash = 0
        
        if isinstance(context.request_data, dict):
            # 会话语言设置
            session_metadata = context.request_data.get("session_metadata", {})
            if isinstance(session_metadata, dict):
                session_lang = session_metadata.get("language")
            
            # 对话内容语言哈希
            dialogue_history = context.request_data.get("dialogue_history", [])
            if isinstance(dialogue_history, list):
                contents = []
                for msg in dialogue_history[-3:]:  # 只考虑最近3条消息
                    if isinstance(msg, dict) and "content" in msg:
                        contents.append(str(msg["content"])[:100])  # 只取前100字符
                content_lang_hash = hash("|".join(contents))
        
        return f"language:{session_lang or 'auto'}:{content_lang_hash}"
