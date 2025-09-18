"""
格式验证策略

基于策略模式的格式验证实现，提供：
- JSON语法验证
- Content-Type检查
- 必需字段验证（session_id, dialogue_history等）
- 字段类型检查
- 数据结构完整性验证
- AgentContext模型验证
"""

import json
import re
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖


class FormatValidationStrategy(IValidationStrategy):
    """格式验证策略 - 检查数据格式和结构完整性"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.require_json_content_type = config.get("require_json_content_type", True)
        self.validate_json_syntax = config.get("validate_json_syntax", True)
        self.validate_required_fields = config.get("validate_required_fields", True)
        self.strict_field_types = config.get("strict_field_types", True)
        
        # 定义AgentContext的必需字段和类型
        self.required_fields = {
            "session_id": str,
            "dialogue_history": list,
            "tool_execution_results": dict,
            "session_metadata": dict
        }
        
        # 定义消息的必需字段
        self.message_required_fields = {
            "role": str,
            "content": str,
            "timestamp": str
        }
        
        # 有效的消息角色
        self.valid_message_roles = {"user", "assistant", "system", "tool"}
        
        # 时间戳格式正则
        self.timestamp_pattern = re.compile(
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$'
        )
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行格式验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        # JSON语法验证（如果数据是字符串）
        if self.validate_json_syntax and isinstance(data, str):
            parsed_data = await self._validate_json_syntax(data, result)
            if parsed_data is None:
                return result  # JSON语法错误，直接返回
            data = parsed_data
        
        # 检查数据是否为字典（AgentContext应该是对象）
        if not isinstance(data, dict):
            error = ValidationError.create_format_error(
                field="root",
                expected_type="对象(object)",
                actual_value=type(data).__name__,
                validator="format"
            )
            result.add_error(error)
            return result
        
        # 验证必需字段
        if self.validate_required_fields:
            await self._validate_required_fields(data, result)
        
        # 验证字段类型
        if self.strict_field_types:
            await self._validate_field_types(data, result)
        
        # 验证对话历史格式
        if "dialogue_history" in data:
            await self._validate_dialogue_history(data["dialogue_history"], result)
        
        # 验证会话元数据格式
        if "session_metadata" in data:
            await self._validate_session_metadata(data["session_metadata"], result)
        
        # 验证工具执行结果格式
        if "tool_execution_results" in data:
            await self._validate_tool_execution_results(data["tool_execution_results"], result)
        
        return result
    
    async def _validate_json_syntax(self, json_str: str, result: ValidationResult) -> Optional[dict]:
        """验证JSON语法"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            error = ValidationError(
                code="INVALID_JSON_SYNTAX",
                message=f"JSON语法错误：{str(e)}",
                validator="format",
                severity=ValidationSeverity.HIGH,
                suggestion="请检查JSON格式，确保括号匹配、引号正确、逗号使用规范",
                metadata={"json_error": str(e), "position": getattr(e, 'pos', None)}
            )
            result.add_error(error)
            return None
    
    async def _validate_required_fields(self, data: dict, result: ValidationResult) -> None:
        """验证必需字段"""
        missing_fields = []
        
        for field_name, field_type in self.required_fields.items():
            if field_name not in data:
                missing_fields.append(field_name)
        
        if missing_fields:
            error = ValidationError(
                code="MISSING_REQUIRED_FIELDS",
                message=f"缺少必需字段：{', '.join(missing_fields)}",
                validator="format",
                severity=ValidationSeverity.HIGH,
                suggestion=f"请确保请求包含所有必需字段：{', '.join(self.required_fields.keys())}",
                metadata={"missing_fields": missing_fields, "required_fields": list(self.required_fields.keys())}
            )
            result.add_error(error)
    
    async def _validate_field_types(self, data: dict, result: ValidationResult) -> None:
        """验证字段类型"""
        for field_name, expected_type in self.required_fields.items():
            if field_name in data:
                actual_value = data[field_name]
                if not isinstance(actual_value, expected_type):
                    error = ValidationError.create_format_error(
                        field=field_name,
                        expected_type=expected_type.__name__,
                        actual_value=type(actual_value).__name__,
                        validator="format"
                    )
                    result.add_error(error)
    
    async def _validate_dialogue_history(self, dialogue_history: Any, result: ValidationResult) -> None:
        """验证对话历史格式"""
        if not isinstance(dialogue_history, list):
            error = ValidationError.create_format_error(
                field="dialogue_history",
                expected_type="数组(array)",
                actual_value=type(dialogue_history).__name__,
                validator="format"
            )
            result.add_error(error)
            return
        
        for i, message in enumerate(dialogue_history):
            await self._validate_message_format(message, i, result)
    
    async def _validate_message_format(self, message: Any, index: int, result: ValidationResult) -> None:
        """验证单条消息格式"""
        field_prefix = f"dialogue_history[{index}]"
        
        # 检查消息是否为对象
        if not isinstance(message, dict):
            error = ValidationError.create_format_error(
                field=field_prefix,
                expected_type="对象(object)",
                actual_value=type(message).__name__,
                validator="format"
            )
            result.add_error(error)
            return
        
        # 检查必需字段
        missing_fields = []
        for field_name in self.message_required_fields:
            if field_name not in message:
                missing_fields.append(field_name)
        
        if missing_fields:
            error = ValidationError(
                code="INVALID_MESSAGE_FORMAT",
                message=f"消息格式错误：第 {index + 1} 条消息缺少字段 {', '.join(missing_fields)}",
                field=field_prefix,
                validator="format",
                severity=ValidationSeverity.HIGH,
                suggestion=f"每条消息必须包含：{', '.join(self.message_required_fields.keys())}",
                metadata={"missing_fields": missing_fields, "message_index": index}
            )
            result.add_error(error)
            return
        
        # 检查字段类型
        for field_name, expected_type in self.message_required_fields.items():
            if field_name in message:
                actual_value = message[field_name]
                if not isinstance(actual_value, expected_type):
                    error = ValidationError.create_format_error(
                        field=f"{field_prefix}.{field_name}",
                        expected_type=expected_type.__name__,
                        actual_value=type(actual_value).__name__,
                        validator="format"
                    )
                    result.add_error(error)
        
        # 验证消息角色
        if "role" in message:
            role = message["role"]
            if role not in self.valid_message_roles:
                error = ValidationError(
                    code="INVALID_MESSAGE_ROLE",
                    message=f"无效的消息角色：'{role}'，有效角色：{', '.join(self.valid_message_roles)}",
                    field=f"{field_prefix}.role",
                    value=role,
                    validator="format",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion=f"请使用有效的消息角色：{', '.join(self.valid_message_roles)}"
                )
                result.add_error(error)
        
        # 验证时间戳格式
        if "timestamp" in message:
            timestamp = message["timestamp"]
            if isinstance(timestamp, str):
                if not self.timestamp_pattern.match(timestamp):
                    error = ValidationError(
                        code="INVALID_TIMESTAMP_FORMAT",
                        message=f"时间戳格式无效：'{timestamp}'",
                        field=f"{field_prefix}.timestamp",
                        value=timestamp,
                        validator="format",
                        severity=ValidationSeverity.MEDIUM,
                        suggestion="请使用ISO 8601格式的时间戳，如：2023-01-01T12:00:00Z"
                    )
                    result.add_error(error)
        
        # 验证assistant消息的tool_calls字段
        if message.get("role") == "assistant" and "tool_calls" in message:
            tool_calls = message["tool_calls"]
            if tool_calls is not None and not isinstance(tool_calls, list):
                error = ValidationError.create_format_error(
                    field=f"{field_prefix}.tool_calls",
                    expected_type="数组(array)或null",
                    actual_value=type(tool_calls).__name__,
                    validator="format"
                )
                result.add_error(error)
        
        # 验证tool消息的tool_call_id字段
        if message.get("role") == "tool":
            if "tool_call_id" not in message:
                error = ValidationError(
                    code="MISSING_TOOL_CALL_ID",
                    message=f"tool类型消息缺少tool_call_id字段：第 {index + 1} 条消息",
                    field=f"{field_prefix}.tool_call_id",
                    validator="format",
                    severity=ValidationSeverity.HIGH,
                    suggestion="tool类型的消息必须包含tool_call_id字段"
                )
                result.add_error(error)
    
    async def _validate_session_metadata(self, metadata: Any, result: ValidationResult) -> None:
        """验证会话元数据格式"""
        if not isinstance(metadata, dict):
            error = ValidationError.create_format_error(
                field="session_metadata",
                expected_type="对象(object)",
                actual_value=type(metadata).__name__,
                validator="format"
            )
            result.add_error(error)
            return
        
        # 验证可选的language字段
        if "language" in metadata:
            language = metadata["language"]
            if not isinstance(language, str):
                error = ValidationError.create_format_error(
                    field="session_metadata.language",
                    expected_type="字符串(string)",
                    actual_value=type(language).__name__,
                    validator="format"
                )
                result.add_error(error)
            elif len(language) < 2 or len(language) > 5:
                error = ValidationError(
                    code="INVALID_LANGUAGE_CODE",
                    message=f"无效的语言代码：'{language}'",
                    field="session_metadata.language",
                    value=language,
                    validator="format",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion="请使用有效的语言代码，如：'en', 'zh', 'es', 'fr', 'ja'"
                )
                result.add_error(error)
    
    async def _validate_tool_execution_results(self, tool_results: Any, result: ValidationResult) -> None:
        """验证工具执行结果格式"""
        if not isinstance(tool_results, dict):
            error = ValidationError.create_format_error(
                field="tool_execution_results",
                expected_type="对象(object)",
                actual_value=type(tool_results).__name__,
                validator="format"
            )
            result.add_error(error)
            return
        
        # 验证工具结果的键名格式
        invalid_keys = []
        for key in tool_results.keys():
            if not isinstance(key, str):
                invalid_keys.append(str(key))
            elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                invalid_keys.append(key)
        
        if invalid_keys:
            error = ValidationError(
                code="INVALID_TOOL_RESULT_KEYS",
                message=f"工具执行结果包含无效的键名：{', '.join(invalid_keys)}",
                field="tool_execution_results",
                validator="format",
                severity=ValidationSeverity.MEDIUM,
                suggestion="工具执行结果的键名应为有效的标识符（字母开头，只包含字母、数字、下划线）",
                metadata={"invalid_keys": invalid_keys}
            )
            result.add_error(error)
    
    def get_strategy_name(self) -> str:
        return "format"


# FormatValidator类已暂时移除，避免BaseValidator依赖
