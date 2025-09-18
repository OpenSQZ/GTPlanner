"""
Pydantic验证适配器

基于适配器模式的Pydantic集成，提供：
- 现有Pydantic模型集成
- AgentContextRequest模型适配
- Pydantic错误到ValidationError转换
- 字段级别错误映射
"""

from typing import Dict, Any, List, Optional, Type, Union
from ..core.interfaces import IValidationStrategy
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)

# 尝试导入Pydantic
try:
    from pydantic import BaseModel, ValidationError as PydanticValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    PydanticValidationError = Exception

# 尝试导入现有的AgentContext模型
try:
    from agent.context_types import AgentContext, Message
    AGENT_CONTEXT_AVAILABLE = True
except ImportError:
    AGENT_CONTEXT_AVAILABLE = False


class PydanticValidationAdapter(IValidationStrategy):
    """Pydantic验证适配器 - 将Pydantic验证集成到验证系统
    
    这个适配器允许复用现有的Pydantic模型验证逻辑，
    并将Pydantic的验证错误转换为统一的ValidationError格式。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_class = config.get("model_class")
        self.strict_validation = config.get("strict_validation", True)
        self.convert_warnings = config.get("convert_warnings", True)
        
        if not PYDANTIC_AVAILABLE:
            print("Warning: Pydantic not available, adapter will be disabled")
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行Pydantic验证
        
        Args:
            data: 待验证的数据
            rules: 验证规则（包含model_class等）
            
        Returns:
            验证结果
        """
        if not PYDANTIC_AVAILABLE:
            return ValidationResult.create_success(metadata={"pydantic_available": False})
        
        # 确定要使用的模型类
        model_class = rules.get("model_class") or self.model_class
        
        if not model_class or not issubclass(model_class, BaseModel):
            error = ValidationError(
                code="INVALID_PYDANTIC_MODEL",
                message="未指定有效的Pydantic模型类",
                validator="pydantic_adapter",
                severity=ValidationSeverity.HIGH,
                suggestion="请指定一个继承自BaseModel的模型类"
            )
            return ValidationResult.create_error(error)
        
        try:
            # 执行Pydantic验证
            if isinstance(data, dict):
                validated_data = model_class(**data)
            else:
                validated_data = model_class.parse_obj(data)
            
            # 验证成功
            return ValidationResult.create_success(metadata={
                "pydantic_validation": "success",
                "model_class": model_class.__name__,
                "validated_data_type": type(validated_data).__name__
            })
            
        except PydanticValidationError as pydantic_error:
            # 转换Pydantic错误
            return self._convert_pydantic_errors(pydantic_error, model_class.__name__)
        
        except Exception as e:
            # 其他异常
            error = ValidationError(
                code="PYDANTIC_VALIDATION_ERROR",
                message=f"Pydantic验证异常: {str(e)}",
                validator="pydantic_adapter",
                severity=ValidationSeverity.HIGH,
                suggestion="请检查数据格式和模型定义"
            )
            return ValidationResult.create_error(error)
    
    def _convert_pydantic_errors(self, pydantic_error: PydanticValidationError, model_name: str) -> ValidationResult:
        """转换Pydantic验证错误
        
        Args:
            pydantic_error: Pydantic验证错误
            model_name: 模型名称
            
        Returns:
            转换后的验证结果
        """
        result = ValidationResult(ValidationStatus.ERROR)
        
        # 处理Pydantic错误列表
        for error_dict in pydantic_error.errors():
            validation_error = self._convert_single_error(error_dict, model_name)
            
            # 根据错误类型决定是错误还是警告
            if self.convert_warnings and self._is_warning_type(error_dict):
                result.add_warning(validation_error)
            else:
                result.add_error(validation_error)
        
        return result
    
    def _convert_single_error(self, error_dict: Dict[str, Any], model_name: str) -> ValidationError:
        """转换单个Pydantic错误
        
        Args:
            error_dict: Pydantic错误字典
            model_name: 模型名称
            
        Returns:
            ValidationError实例
        """
        # 提取错误信息
        error_type = error_dict.get("type", "unknown")
        error_msg = error_dict.get("msg", "未知验证错误")
        error_loc = error_dict.get("loc", ())
        error_input = error_dict.get("input")
        
        # 构建字段路径
        field_path = ".".join(str(loc) for loc in error_loc) if error_loc else None
        
        # 映射Pydantic错误类型到我们的错误代码
        error_code = self._map_pydantic_error_type(error_type)
        
        # 确定严重程度
        severity = self._determine_error_severity(error_type)
        
        # 生成建议信息
        suggestion = self._generate_suggestion(error_type, field_path, error_input)
        
        return ValidationError(
            code=error_code,
            message=f"字段验证失败: {error_msg}",
            field=field_path,
            value=error_input,
            validator="pydantic_adapter",
            severity=severity,
            suggestion=suggestion,
            metadata={
                "pydantic_type": error_type,
                "pydantic_msg": error_msg,
                "model_name": model_name,
                "field_location": list(error_loc)
            }
        )
    
    def _map_pydantic_error_type(self, pydantic_type: str) -> str:
        """映射Pydantic错误类型到错误代码
        
        Args:
            pydantic_type: Pydantic错误类型
            
        Returns:
            映射的错误代码
        """
        error_type_mapping = {
            "missing": "MISSING_FIELD",
            "value_error": "INVALID_VALUE",
            "type_error": "INVALID_TYPE",
            "assertion_error": "ASSERTION_FAILED",
            "value_error.missing": "MISSING_REQUIRED_VALUE",
            "value_error.extra": "EXTRA_FIELD_NOT_ALLOWED",
            "value_error.str.regex": "STRING_PATTERN_MISMATCH",
            "value_error.number.not_gt": "NUMBER_TOO_SMALL",
            "value_error.number.not_lt": "NUMBER_TOO_LARGE",
            "value_error.list.min_items": "LIST_TOO_SHORT",
            "value_error.list.max_items": "LIST_TOO_LONG",
            "value_error.str.min_length": "STRING_TOO_SHORT",
            "value_error.str.max_length": "STRING_TOO_LONG",
            "type_error.integer": "EXPECTED_INTEGER",
            "type_error.float": "EXPECTED_FLOAT",
            "type_error.str": "EXPECTED_STRING",
            "type_error.bool": "EXPECTED_BOOLEAN",
            "type_error.list": "EXPECTED_LIST",
            "type_error.dict": "EXPECTED_DICT"
        }
        
        return error_type_mapping.get(pydantic_type, f"PYDANTIC_{pydantic_type.upper()}")
    
    def _determine_error_severity(self, pydantic_type: str) -> ValidationSeverity:
        """确定错误严重程度
        
        Args:
            pydantic_type: Pydantic错误类型
            
        Returns:
            错误严重程度
        """
        # 关键错误类型
        critical_types = ["missing", "type_error"]
        high_types = ["value_error", "assertion_error"]
        medium_types = ["value_error.extra", "value_error.str.regex"]
        
        if any(pydantic_type.startswith(t) for t in critical_types):
            return ValidationSeverity.CRITICAL
        elif any(pydantic_type.startswith(t) for t in high_types):
            return ValidationSeverity.HIGH
        elif any(pydantic_type.startswith(t) for t in medium_types):
            return ValidationSeverity.MEDIUM
        else:
            return ValidationSeverity.LOW
    
    def _generate_suggestion(self, pydantic_type: str, field_path: Optional[str], error_input: Any) -> str:
        """生成修复建议
        
        Args:
            pydantic_type: Pydantic错误类型
            field_path: 字段路径
            error_input: 错误输入值
            
        Returns:
            修复建议字符串
        """
        field_name = field_path or "该字段"
        
        suggestion_templates = {
            "missing": f"请提供必需的字段 '{field_name}'",
            "type_error.integer": f"请为字段 '{field_name}' 提供整数值",
            "type_error.float": f"请为字段 '{field_name}' 提供数字值",
            "type_error.str": f"请为字段 '{field_name}' 提供字符串值",
            "type_error.bool": f"请为字段 '{field_name}' 提供布尔值（true/false）",
            "type_error.list": f"请为字段 '{field_name}' 提供数组值",
            "type_error.dict": f"请为字段 '{field_name}' 提供对象值",
            "value_error.str.min_length": f"字段 '{field_name}' 的值太短，请增加内容",
            "value_error.str.max_length": f"字段 '{field_name}' 的值太长，请减少内容",
            "value_error.list.min_items": f"字段 '{field_name}' 的数组元素太少",
            "value_error.list.max_items": f"字段 '{field_name}' 的数组元素太多",
            "value_error.number.not_gt": f"字段 '{field_name}' 的值太小",
            "value_error.number.not_lt": f"字段 '{field_name}' 的值太大",
            "value_error.extra": f"字段 '{field_name}' 不是允许的字段，请移除"
        }
        
        return suggestion_templates.get(pydantic_type, f"请检查字段 '{field_name}' 的格式和值")
    
    def _is_warning_type(self, error_dict: Dict[str, Any]) -> bool:
        """判断是否为警告类型的错误
        
        Args:
            error_dict: Pydantic错误字典
            
        Returns:
            True表示警告，False表示错误
        """
        warning_types = ["value_error.extra"]  # 额外字段通常作为警告处理
        error_type = error_dict.get("type", "")
        return error_type in warning_types
    
    def get_strategy_name(self) -> str:
        return "pydantic_adapter"


class AgentContextPydanticAdapter:
    """AgentContext Pydantic适配器 - 专门用于AgentContext验证"""
    
    def __init__(self):
        self.adapter = PydanticValidationAdapter({
            "strict_validation": True,
            "convert_warnings": True
        })
    
    async def validate_agent_context(self, data: Dict[str, Any]) -> ValidationResult:
        """验证AgentContext数据
        
        Args:
            data: AgentContext数据字典
            
        Returns:
            验证结果
        """
        if not AGENT_CONTEXT_AVAILABLE:
            return ValidationResult.create_success(metadata={"agent_context_available": False})
        
        try:
            # 使用现有的AgentContext模型进行验证
            agent_context = AgentContext.from_dict(data)
            
            # 验证成功
            return ValidationResult.create_success(metadata={
                "agent_context_validation": "success",
                "session_id": agent_context.session_id,
                "dialogue_history_length": len(agent_context.dialogue_history),
                "is_compressed": agent_context.is_compressed
            })
            
        except Exception as e:
            # 转换为标准验证错误
            error = ValidationError(
                code="AGENT_CONTEXT_VALIDATION_ERROR",
                message=f"AgentContext验证失败: {str(e)}",
                validator="agent_context_adapter",
                severity=ValidationSeverity.HIGH,
                suggestion="请检查AgentContext数据格式，确保包含所有必需字段"
            )
            return ValidationResult.create_error(error)
    
    async def validate_message_list(self, messages: List[Dict[str, Any]]) -> ValidationResult:
        """验证消息列表
        
        Args:
            messages: 消息字典列表
            
        Returns:
            验证结果
        """
        if not AGENT_CONTEXT_AVAILABLE:
            return ValidationResult.create_success()
        
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        for i, message_data in enumerate(messages):
            try:
                # 使用现有的Message模型进行验证
                message = Message.from_dict(message_data)
                
                # 验证消息的特定规则
                await self._validate_message_rules(message, i, result)
                
            except Exception as e:
                error = ValidationError(
                    code="MESSAGE_VALIDATION_ERROR",
                    message=f"消息 {i+1} 验证失败: {str(e)}",
                    field=f"dialogue_history[{i}]",
                    validator="message_adapter",
                    severity=ValidationSeverity.HIGH,
                    suggestion="请检查消息格式，确保包含role、content、timestamp字段"
                )
                result.add_error(error)
        
        return result
    
    async def _validate_message_rules(self, message: 'Message', index: int, result: ValidationResult) -> None:
        """验证消息的业务规则
        
        Args:
            message: 消息对象
            index: 消息索引
            result: 验证结果
        """
        # 验证消息内容不为空
        if not message.content or not message.content.strip():
            error = ValidationError(
                code="EMPTY_MESSAGE_CONTENT",
                message=f"消息 {index+1} 内容为空",
                field=f"dialogue_history[{index}].content",
                validator="message_adapter",
                severity=ValidationSeverity.MEDIUM,
                suggestion="请提供有意义的消息内容"
            )
            result.add_warning(error)
        
        # 验证时间戳格式
        if message.timestamp:
            try:
                from datetime import datetime
                # 尝试解析时间戳
                datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
            except ValueError:
                error = ValidationError(
                    code="INVALID_TIMESTAMP_FORMAT",
                    message=f"消息 {index+1} 时间戳格式无效",
                    field=f"dialogue_history[{index}].timestamp",
                    value=message.timestamp,
                    validator="message_adapter",
                    severity=ValidationSeverity.MEDIUM,
                    suggestion="请使用ISO 8601格式的时间戳"
                )
                result.add_error(error)
        
        # 验证tool消息的tool_call_id
        if hasattr(message, 'role') and message.role.value == "tool":
            if not hasattr(message, 'tool_call_id') or not message.tool_call_id:
                error = ValidationError(
                    code="MISSING_TOOL_CALL_ID",
                    message=f"tool类型消息 {index+1} 缺少tool_call_id",
                    field=f"dialogue_history[{index}].tool_call_id",
                    validator="message_adapter",
                    severity=ValidationSeverity.HIGH,
                    suggestion="tool类型的消息必须包含tool_call_id字段"
                )
                result.add_error(error)


def create_pydantic_adapter(model_class: Optional[Type[BaseModel]] = None, config: Optional[Dict[str, Any]] = None) -> PydanticValidationAdapter:
    """创建Pydantic适配器的便捷函数
    
    Args:
        model_class: Pydantic模型类
        config: 适配器配置
        
    Returns:
        Pydantic适配器实例
    """
    adapter_config = config or {}
    if model_class:
        adapter_config["model_class"] = model_class
    
    return PydanticValidationAdapter(adapter_config)


def create_agent_context_adapter() -> AgentContextPydanticAdapter:
    """创建AgentContext适配器的便捷函数
    
    Returns:
        AgentContext适配器实例
    """
    return AgentContextPydanticAdapter()


# 预定义的验证函数
async def validate_with_agent_context(data: Dict[str, Any]) -> ValidationResult:
    """使用AgentContext模型验证数据
    
    Args:
        data: 待验证的数据
        
    Returns:
        验证结果
    """
    adapter = create_agent_context_adapter()
    return await adapter.validate_agent_context(data)


async def validate_dialogue_history(messages: List[Dict[str, Any]]) -> ValidationResult:
    """验证对话历史
    
    Args:
        messages: 消息列表
        
    Returns:
        验证结果
    """
    adapter = create_agent_context_adapter()
    return await adapter.validate_message_list(messages)
