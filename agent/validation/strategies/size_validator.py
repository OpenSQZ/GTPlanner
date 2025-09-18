"""
大小验证策略

基于策略模式的大小验证实现，提供：
- Content-Length头验证
- 请求体大小检查
- JSON深度限制
- 数组长度限制
- 消息内容长度验证
- 对话历史长度限制
"""

import json
import sys
from typing import Dict, Any, List, Optional, Union
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖


class SizeValidationStrategy(IValidationStrategy):
    """大小验证策略 - 检查各种大小限制"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_request_size = config.get("max_request_size", 1048576)  # 1MB
        self.max_content_length = config.get("max_content_length", 1048576)  # 1MB
        self.max_json_depth = config.get("max_json_depth", 10)
        self.max_array_length = config.get("max_array_length", 1000)
        self.max_string_length = config.get("max_string_length", 10000)
        self.max_dialogue_history_length = config.get("max_dialogue_history_length", 50)
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行大小验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        # 检查请求体大小
        await self._check_request_size(data, result)
        
        # 检查JSON结构深度
        if isinstance(data, (dict, list)):
            await self._check_json_depth(data, result)
        
        # 检查数组长度
        if isinstance(data, dict):
            await self._check_array_lengths(data, result)
        
        # 检查字符串长度
        await self._check_string_lengths(data, result)
        
        # 检查特定字段（如对话历史）
        if isinstance(data, dict):
            await self._check_specific_fields(data, result)
        
        return result
    
    async def _check_request_size(self, data: Any, result: ValidationResult) -> None:
        """检查请求大小"""
        try:
            # 计算数据的字节大小
            if isinstance(data, str):
                size = len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                # 序列化为JSON来计算大小
                json_str = json.dumps(data, ensure_ascii=False)
                size = len(json_str.encode('utf-8'))
            else:
                size = sys.getsizeof(data)
            
            if size > self.max_request_size:
                error = ValidationError.create_size_error(
                    current_size=size,
                    max_size=self.max_request_size,
                    field="request_body",
                    validator="size"
                )
                result.add_error(error)
        
        except Exception as e:
            # 如果无法计算大小，添加警告
            error = ValidationError(
                code="SIZE_CALCULATION_ERROR",
                message=f"无法计算请求大小: {str(e)}",
                validator="size",
                severity=ValidationSeverity.LOW,
                suggestion="请检查请求数据格式"
            )
            result.add_warning(error)
    
    async def _check_json_depth(self, data: Union[dict, list], result: ValidationResult, current_depth: int = 0) -> None:
        """检查JSON嵌套深度"""
        if current_depth > self.max_json_depth:
            error = ValidationError(
                code="JSON_DEPTH_EXCEEDED",
                message=f"JSON嵌套深度超出限制：当前 {current_depth} 层，最大允许 {self.max_json_depth} 层",
                validator="size",
                severity=ValidationSeverity.HIGH,
                suggestion=f"请减少JSON嵌套层级至 {self.max_json_depth} 层以内"
            )
            result.add_error(error)
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    await self._check_json_depth(value, result, current_depth + 1)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    await self._check_json_depth(item, result, current_depth + 1)
    
    async def _check_array_lengths(self, data: dict, result: ValidationResult, path: str = "") -> None:
        """检查数组长度"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, list):
                if len(value) > self.max_array_length:
                    error = ValidationError(
                        code="ARRAY_LENGTH_EXCEEDED",
                        message=f"数组长度超出限制：字段 '{current_path}' 长度 {len(value)}，最大允许 {self.max_array_length}",
                        field=current_path,
                        value=len(value),
                        validator="size",
                        severity=ValidationSeverity.HIGH,
                        suggestion=f"请将数组 '{current_path}' 长度控制在 {self.max_array_length} 以内"
                    )
                    result.add_error(error)
                
                # 递归检查数组中的对象
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        await self._check_array_lengths(item, result, f"{current_path}[{i}]")
            
            elif isinstance(value, dict):
                await self._check_array_lengths(value, result, current_path)
    
    async def _check_string_lengths(self, data: Any, result: ValidationResult, path: str = "") -> None:
        """检查字符串长度"""
        if isinstance(data, str):
            if len(data) > self.max_string_length:
                error = ValidationError(
                    code="STRING_LENGTH_EXCEEDED",
                    message=f"字符串长度超出限制：{'字段 ' + path if path else '内容'} 长度 {len(data)}，最大允许 {self.max_string_length}",
                    field=path or "content",
                    value=len(data),
                    validator="size",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion=f"请将{'字段 ' + path if path else '内容'}长度控制在 {self.max_string_length} 字符以内"
                )
                result.add_error(error)
        
        elif isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                await self._check_string_lengths(value, result, current_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                await self._check_string_lengths(item, result, current_path)
    
    async def _check_specific_fields(self, data: dict, result: ValidationResult) -> None:
        """检查特定字段的大小限制"""
        # 检查对话历史长度
        if "dialogue_history" in data:
            dialogue_history = data["dialogue_history"]
            if isinstance(dialogue_history, list):
                if len(dialogue_history) > self.max_dialogue_history_length:
                    error = ValidationError(
                        code="DIALOGUE_HISTORY_TOO_LONG",
                        message=f"对话历史过长：当前 {len(dialogue_history)} 条消息，最大允许 {self.max_dialogue_history_length} 条",
                        field="dialogue_history",
                        value=len(dialogue_history),
                        validator="size",
                        severity=ValidationSeverity.MEDIUM,
                        suggestion=f"请将对话历史控制在 {self.max_dialogue_history_length} 条消息以内，或使用智能压缩"
                    )
                    result.add_error(error)
                
                # 检查单条消息长度
                for i, message in enumerate(dialogue_history):
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                        if isinstance(content, str) and len(content) > self.max_string_length:
                            error = ValidationError(
                                code="MESSAGE_CONTENT_TOO_LONG",
                                message=f"消息内容过长：第 {i+1} 条消息长度 {len(content)}，最大允许 {self.max_string_length}",
                                field=f"dialogue_history[{i}].content",
                                value=len(content),
                                validator="size",
                                severity=ValidationSeverity.MEDIUM,
                                suggestion=f"请将单条消息长度控制在 {self.max_string_length} 字符以内"
                            )
                            result.add_error(error)
        
        # 检查工具执行结果大小
        if "tool_execution_results" in data:
            tool_results = data["tool_execution_results"]
            if isinstance(tool_results, dict):
                try:
                    results_str = json.dumps(tool_results, ensure_ascii=False)
                    results_size = len(results_str.encode('utf-8'))
                    max_tool_results_size = self.config.get("max_tool_results_size", 512000)  # 512KB
                    
                    if results_size > max_tool_results_size:
                        error = ValidationError(
                            code="TOOL_RESULTS_TOO_LARGE",
                            message=f"工具执行结果过大：当前 {results_size} 字节，最大允许 {max_tool_results_size} 字节",
                            field="tool_execution_results",
                            value=results_size,
                            validator="size",
                            severity=ValidationSeverity.MEDIUM,
                            suggestion=f"请减少工具执行结果的大小至 {max_tool_results_size} 字节以内"
                        )
                        result.add_error(error)
                
                except Exception:
                    # 如果无法序列化工具结果，添加警告
                    error = ValidationError(
                        code="TOOL_RESULTS_SERIALIZATION_ERROR",
                        message="无法序列化工具执行结果以检查大小",
                        field="tool_execution_results",
                        validator="size",
                        severity=ValidationSeverity.LOW,
                        suggestion="请检查工具执行结果的数据格式"
                    )
                    result.add_warning(error)
    
    def get_strategy_name(self) -> str:
        return "size"


# SizeValidator类已暂时移除，避免BaseValidator依赖
