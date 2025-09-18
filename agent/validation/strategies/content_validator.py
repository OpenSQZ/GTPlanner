"""
内容验证策略

基于策略模式的内容验证实现，提供：
- 消息内容长度检查
- 对话历史长度限制
- 垃圾信息检测
- 内容质量评估
- 多语言内容一致性检查
- 重复内容检测
- 空内容检查
"""

import re
from typing import Dict, Any, List, Optional, Set
from collections import Counter
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖


class ContentValidationStrategy(IValidationStrategy):
    """内容验证策略 - 检查内容质量和合规性"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_message_length = config.get("max_message_length", 10000)
        self.max_dialogue_history_length = config.get("max_dialogue_history_length", 50)
        self.enable_profanity_filter = config.get("enable_profanity_filter", False)
        self.enable_spam_detection = config.get("enable_spam_detection", True)
        self.min_content_length = config.get("min_content_length", 1)
        self.max_repetition_ratio = config.get("max_repetition_ratio", 0.8)
        
        # 垃圾信息检测模式
        self.spam_patterns = self._compile_spam_patterns()
        
        # 低质量内容模式
        self.low_quality_patterns = self._compile_low_quality_patterns()
        
        # 常见的测试内容
        self.test_content_patterns = self._compile_test_patterns()
    
    def _compile_spam_patterns(self) -> List[re.Pattern]:
        """编译垃圾信息检测模式"""
        patterns = [
            # 重复字符
            r'(.)\1{10,}',  # 同一字符重复超过10次
            # 重复词语
            r'\b(\w+)\s+\1\s+\1',  # 同一词语连续重复3次
            # 大量标点符号
            r'[!@#$%^&*()_+={}\[\]|\\:";\'<>?,./-]{20,}',
            # 全大写（超过一定长度）
            r'\b[A-Z]{20,}\b',
            # 大量数字
            r'\d{50,}',
            # 网址模式（如果需要过滤）
            r'https?://[^\s]+',
            # 邮箱模式（如果需要过滤）
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_low_quality_patterns(self) -> List[re.Pattern]:
        """编译低质量内容模式"""
        patterns = [
            # 纯符号
            r'^[^a-zA-Z0-9\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+$',
            # 纯空白字符
            r'^\s+$',
            # 单字符重复
            r'^(.)\1*$',
        ]
        return [re.compile(pattern) for pattern in patterns]
    
    def _compile_test_patterns(self) -> List[re.Pattern]:
        """编译测试内容模式"""
        patterns = [
            r'^test\s*\d*$',
            r'^hello\s*world\s*!*$',
            r'^测试\s*\d*$',
            r'^aaa+$',
            r'^111+$',
            r'^.*test.*test.*$',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行内容验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        if not isinstance(data, dict):
            return result
        
        # 验证对话历史内容
        if "dialogue_history" in data:
            await self._validate_dialogue_content(data["dialogue_history"], result)
        
        # 验证会话元数据内容
        if "session_metadata" in data:
            await self._validate_metadata_content(data["session_metadata"], result)
        
        return result
    
    async def _validate_dialogue_content(self, dialogue_history: Any, result: ValidationResult) -> None:
        """验证对话历史内容"""
        if not isinstance(dialogue_history, list):
            return
        
        # 检查对话历史长度
        if len(dialogue_history) > self.max_dialogue_history_length:
            error = ValidationError(
                code="DIALOGUE_HISTORY_TOO_LONG",
                message=f"对话历史过长：{len(dialogue_history)} 条消息，建议不超过 {self.max_dialogue_history_length} 条",
                field="dialogue_history",
                value=len(dialogue_history),
                validator="content",
                severity=ValidationSeverity.MEDIUM,
                suggestion=f"请控制对话历史长度在 {self.max_dialogue_history_length} 条以内，可使用智能压缩"
            )
            result.add_warning(error)  # 作为警告处理
        
        # 检查重复消息
        await self._check_duplicate_messages(dialogue_history, result)
        
        # 逐条验证消息内容
        for i, message in enumerate(dialogue_history):
            if isinstance(message, dict) and "content" in message:
                await self._validate_message_content(message["content"], i, result)
    
    async def _check_duplicate_messages(self, dialogue_history: List[Any], result: ValidationResult) -> None:
        """检查重复消息"""
        content_counts = Counter()
        
        for message in dialogue_history:
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                if isinstance(content, str) and len(content.strip()) > 0:
                    # 标准化内容（去除空白字符差异）
                    normalized_content = re.sub(r'\s+', ' ', content.strip().lower())
                    content_counts[normalized_content] += 1
        
        # 查找重复内容
        duplicates = {content: count for content, count in content_counts.items() if count > 1}
        
        if duplicates:
            duplicate_info = [f"'{content[:50]}...' ({count}次)" for content, count in duplicates.items()]
            error = ValidationError(
                code="DUPLICATE_MESSAGES_DETECTED",
                message=f"检测到重复消息：{', '.join(duplicate_info)}",
                field="dialogue_history",
                validator="content",
                severity=ValidationSeverity.LOW,
                suggestion="请避免发送重复的消息内容",
                metadata={"duplicate_count": len(duplicates), "duplicates": list(duplicates.keys())}
            )
            result.add_warning(error)
    
    async def _validate_message_content(self, content: Any, index: int, result: ValidationResult) -> None:
        """验证单条消息内容"""
        if not isinstance(content, str):
            return
        
        field_name = f"dialogue_history[{index}].content"
        
        # 检查内容长度
        if len(content) > self.max_message_length:
            error = ValidationError(
                code="MESSAGE_CONTENT_TOO_LONG",
                message=f"消息内容过长：第 {index + 1} 条消息 {len(content)} 字符，最大允许 {self.max_message_length}",
                field=field_name,
                value=len(content),
                validator="content",
                severity=ValidationSeverity.MEDIUM,
                suggestion=f"请将消息长度控制在 {self.max_message_length} 字符以内"
            )
            result.add_error(error)
        
        # 检查最小内容长度
        stripped_content = content.strip()
        if len(stripped_content) < self.min_content_length:
            error = ValidationError(
                code="MESSAGE_CONTENT_TOO_SHORT",
                message=f"消息内容过短：第 {index + 1} 条消息内容为空或过短",
                field=field_name,
                validator="content",
                severity=ValidationSeverity.LOW,
                suggestion="请提供有意义的消息内容"
            )
            result.add_warning(error)
            return  # 内容太短，跳过其他检查
        
        # 垃圾信息检测
        if self.enable_spam_detection:
            await self._check_spam_content(stripped_content, field_name, result)
        
        # 低质量内容检测
        await self._check_low_quality_content(stripped_content, field_name, result)
        
        # 测试内容检测
        await self._check_test_content(stripped_content, field_name, result)
        
        # 重复字符检测
        await self._check_repetitive_content(stripped_content, field_name, result)
    
    async def _check_spam_content(self, content: str, field_name: str, result: ValidationResult) -> None:
        """检查垃圾信息"""
        for pattern in self.spam_patterns:
            if pattern.search(content):
                error = ValidationError(
                    code="SPAM_CONTENT_DETECTED",
                    message="检测到可能的垃圾信息或低质量内容",
                    field=field_name,
                    validator="content",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion="请提供有意义、高质量的内容，避免重复字符、符号堆砌等",
                    metadata={"pattern": pattern.pattern}
                )
                result.add_warning(error)
                break  # 只报告第一个匹配的垃圾信息模式
    
    async def _check_low_quality_content(self, content: str, field_name: str, result: ValidationResult) -> None:
        """检查低质量内容"""
        for pattern in self.low_quality_patterns:
            if pattern.match(content):
                error = ValidationError(
                    code="LOW_QUALITY_CONTENT",
                    message="检测到低质量内容（纯符号、空白字符或单字符重复）",
                    field=field_name,
                    validator="content",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion="请提供包含有效文字信息的内容",
                    metadata={"pattern": pattern.pattern}
                )
                result.add_warning(error)
                break
    
    async def _check_test_content(self, content: str, field_name: str, result: ValidationResult) -> None:
        """检查测试内容"""
        for pattern in self.test_content_patterns:
            if pattern.match(content):
                error = ValidationError(
                    code="TEST_CONTENT_DETECTED",
                    message="检测到测试内容，建议使用实际的用户输入",
                    field=field_name,
                    validator="content",
                    severity=ValidationSeverity.LOW,
                    suggestion="请使用真实的用户输入而不是测试内容",
                    metadata={"pattern": pattern.pattern}
                )
                result.add_warning(error)
                break
    
    async def _check_repetitive_content(self, content: str, field_name: str, result: ValidationResult) -> None:
        """检查重复内容比例"""
        if len(content) < 20:  # 内容太短，跳过重复检查
            return
        
        # 计算字符重复比例
        char_counts = Counter(content.lower())
        total_chars = len(content)
        max_char_count = max(char_counts.values()) if char_counts else 0
        repetition_ratio = max_char_count / total_chars if total_chars > 0 else 0
        
        if repetition_ratio > self.max_repetition_ratio:
            most_common_char = char_counts.most_common(1)[0][0]
            error = ValidationError(
                code="HIGHLY_REPETITIVE_CONTENT",
                message=f"内容重复度过高：字符 '{most_common_char}' 占比 {repetition_ratio:.1%}",
                field=field_name,
                validator="content",
                severity=ValidationSeverity.MEDIUM,
                suggestion=f"请减少重复字符，保持重复度在 {self.max_repetition_ratio:.0%} 以下",
                metadata={
                    "repetition_ratio": repetition_ratio,
                    "most_common_char": most_common_char,
                    "char_count": max_char_count
                }
            )
            result.add_warning(error)
    
    async def _validate_metadata_content(self, metadata: Any, result: ValidationResult) -> None:
        """验证会话元数据内容"""
        if not isinstance(metadata, dict):
            return
        
        # 检查元数据中的字符串值
        for key, value in metadata.items():
            if isinstance(value, str) and len(value.strip()) == 0:
                error = ValidationError(
                    code="EMPTY_METADATA_VALUE",
                    message=f"会话元数据包含空值：字段 '{key}'",
                    field=f"session_metadata.{key}",
                    validator="content",
                    severity=ValidationSeverity.LOW,
                    suggestion="请移除空的元数据字段或提供有效值"
                )
                result.add_warning(error)
    
    def get_strategy_name(self) -> str:
        return "content"


# class ContentValidator(BaseValidator):  # 暂时注释避免dynaconf依赖
    """内容验证器 - 基于BaseValidator的完整实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.strategy = ContentValidationStrategy(config)
    
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        """执行内容验证逻辑"""
        return await self.strategy.execute(context.request_data, context.validation_rules)
    
    def get_validator_name(self) -> str:
        return "content"
    
    def get_priority(self) -> ValidatorPriority:
        return ValidatorPriority.MEDIUM
    
    def can_cache_result(self) -> bool:
        # 内容验证结果可以缓存，但TTL应该较短
        return self.config.get("enable_cache", True)
    
    def get_cache_key(self, context: ValidationContext) -> Optional[str]:
        """生成内容验证的缓存键"""
        if not self.can_cache_result():
            return None
        
        try:
            # 基于内容哈希生成缓存键
            if isinstance(context.request_data, dict):
                dialogue_history = context.request_data.get("dialogue_history", [])
                if isinstance(dialogue_history, list) and dialogue_history:
                    # 提取所有消息内容
                    contents = []
                    for msg in dialogue_history:
                        if isinstance(msg, dict) and "content" in msg:
                            contents.append(str(msg["content"]))
                    
                    if contents:
                        content_hash = hash("|".join(contents))
                        return f"content:{content_hash}:{len(contents)}"
                
                return f"content:{hash(str(context.request_data))}"
            
            return f"content:{hash(str(context.request_data))}"
        
        except Exception:
            return None
