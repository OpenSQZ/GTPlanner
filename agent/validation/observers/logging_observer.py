"""
日志观察者

基于观察者模式的日志记录实现，提供：
- 集成现有日志系统
- 验证事件日志记录
- 性能指标日志
- 错误详情日志
- 可配置的日志级别
"""

import json
import time
from typing import Dict, Any, Optional
from ..core.interfaces import IValidationObserver
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult, ValidationStatus

# 尝试导入现有的日志系统
try:
    from utils.logger_config import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    print("Warning: Logger not available, using print for logging")


class LoggingObserver(IValidationObserver):
    """日志观察者 - 记录验证过程的详细日志
    
    集成GTPlanner现有的日志系统，提供：
    - 验证事件的结构化日志记录
    - 可配置的日志级别和内容
    - 性能指标的自动记录
    - 错误详情的安全记录
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 日志配置
        self.enabled = self.config.get("enabled", True)
        self.log_level = self.config.get("level", "INFO").upper()
        self.include_request_details = self.config.get("include_request_details", True)
        self.include_validation_path = self.config.get("include_validation_path", True)
        self.include_performance_metrics = self.config.get("include_performance_metrics", True)
        self.log_successful_validations = self.config.get("log_successful_validations", False)
        self.log_failed_validations = self.config.get("log_failed_validations", True)
        self.max_content_length = self.config.get("max_content_length", 200)
        self.mask_sensitive_data = self.config.get("mask_sensitive_data", True)
        
        # 初始化日志器
        if LOGGER_AVAILABLE:
            self.logger = get_logger("validation")
        else:
            self.logger = None
    
    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外信息
        """
        if not self.enabled:
            return
        
        if self.logger:
            # 使用现有日志系统
            log_func = getattr(self.logger, level.lower(), self.logger.info)
            if extra:
                log_func(f"{message} | {json.dumps(extra, ensure_ascii=False)}")
            else:
                log_func(message)
        else:
            # 回退到print
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            extra_str = f" | {json.dumps(extra, ensure_ascii=False)}" if extra else ""
            print(f"[{timestamp}] {level} - validation - {message}{extra_str}")
    
    async def on_validation_start(self, context: ValidationContext) -> None:
        """验证开始事件
        
        Args:
            context: 验证上下文
        """
        if not self.enabled:
            return
        
        message = f"验证开始 - 请求ID: {context.request_id}"
        extra = {}
        
        if self.include_request_details:
            extra.update({
                "method": context.request_method,
                "path": context.request_path,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "client_ip": context.client_ip,
                "validation_mode": context.validation_mode.value,
                "language": context.get_language_preference()
            })
        
        # 添加请求数据摘要（安全地）
        if context.request_data and self.include_request_details:
            extra["request_data_summary"] = self._create_data_summary(context.request_data)
        
        self._log("INFO", message, extra)
    
    async def on_validation_step(self, validator_name: str, result: ValidationResult) -> None:
        """验证步骤完成事件
        
        Args:
            validator_name: 验证器名称
            result: 验证结果
        """
        if not self.enabled:
            return
        
        # 根据结果状态决定日志级别
        if result.status == ValidationStatus.SUCCESS:
            if not self.log_successful_validations:
                return
            level = "DEBUG"
            message = f"验证器 {validator_name} 通过"
        elif result.status == ValidationStatus.WARNING:
            level = "WARNING"
            message = f"验证器 {validator_name} 有警告"
        else:
            level = "WARNING"
            message = f"验证器 {validator_name} 失败"
        
        extra = {
            "validator": validator_name,
            "status": result.status.value,
            "has_errors": result.has_errors,
            "has_warnings": result.has_warnings,
            "execution_time": result.execution_time
        }
        
        # 添加错误详情
        if result.has_errors and self.log_failed_validations:
            extra["errors"] = [
                {
                    "code": error.code,
                    "message": error.message[:self.max_content_length],
                    "severity": error.severity.name
                }
                for error in result.errors[:3]  # 只记录前3个错误
            ]
        
        # 添加警告详情
        if result.has_warnings:
            extra["warnings"] = [
                {
                    "code": warning.code,
                    "message": warning.message[:self.max_content_length]
                }
                for warning in result.warnings[:2]  # 只记录前2个警告
            ]
        
        self._log(level, message, extra)
    
    async def on_validation_complete(self, result: ValidationResult) -> None:
        """验证完成事件
        
        Args:
            result: 最终验证结果
        """
        if not self.enabled:
            return
        
        # 根据最终结果决定日志级别和内容
        if result.is_valid:
            if not self.log_successful_validations:
                return
            level = "INFO"
            message = f"验证完成 - 状态: {result.status.value}"
        else:
            level = "WARNING"
            message = f"验证失败 - 状态: {result.status.value}"
        
        extra = {
            "request_id": result.request_id,
            "status": result.status.value,
            "is_valid": result.is_valid,
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
            "execution_time": result.execution_time
        }
        
        # 添加验证路径
        if self.include_validation_path:
            extra["validation_path"] = result.execution_order
            extra["failed_validators"] = result.get_failed_validators()
        
        # 添加性能指标
        if self.include_performance_metrics:
            extra["metrics"] = {
                "executed_validators": result.metrics.executed_validators,
                "skipped_validators": result.metrics.skipped_validators,
                "success_rate": result.metrics.get_success_rate(),
                "cache_hit_rate": result.metrics.get_cache_hit_rate()
            }
        
        # 添加错误摘要（不包含敏感信息）
        if result.has_errors and self.log_failed_validations:
            error_summary = result.get_error_summary()
            extra["error_summary"] = error_summary
            
            # 添加关键错误详情
            critical_errors = [
                error for error in result.errors 
                if error.severity.value >= 3  # HIGH或CRITICAL
            ]
            
            if critical_errors:
                extra["critical_errors"] = [
                    {
                        "code": error.code,
                        "message": error.message[:self.max_content_length],
                        "severity": error.severity.name,
                        "validator": error.validator
                    }
                    for error in critical_errors[:3]
                ]
        
        self._log(level, message, extra)
    
    async def on_validation_error(self, error: Exception, context: Optional[ValidationContext] = None) -> None:
        """验证错误事件
        
        Args:
            error: 发生的异常
            context: 验证上下文（可能为None）
        """
        if not self.enabled:
            return
        
        message = f"验证系统错误: {type(error).__name__}"
        
        extra = {
            "error_type": type(error).__name__,
            "error_message": str(error)[:self.max_content_length]
        }
        
        if context:
            extra.update({
                "request_id": context.request_id,
                "request_path": context.request_path,
                "request_method": context.request_method,
                "current_validator": context.current_validator,
                "validation_path": context.validation_path,
                "execution_time": context.get_execution_time()
            })
        
        # 添加堆栈跟踪（仅用于调试）
        if not self.mask_sensitive_data:
            extra["stack_trace"] = traceback.format_exc()
        
        self._log("ERROR", message, extra)
    
    def _create_data_summary(self, data: Any) -> Dict[str, Any]:
        """创建数据摘要（安全地，不包含敏感信息）
        
        Args:
            data: 请求数据
            
        Returns:
            数据摘要字典
        """
        if isinstance(data, dict):
            summary = {
                "type": "object",
                "keys": list(data.keys()),
                "key_count": len(data)
            }
            
            # 添加特定字段的摘要
            if "dialogue_history" in data:
                dialogue_history = data["dialogue_history"]
                if isinstance(dialogue_history, list):
                    summary["dialogue_history_length"] = len(dialogue_history)
                    
                    # 最后一条消息的角色
                    if dialogue_history:
                        last_message = dialogue_history[-1]
                        if isinstance(last_message, dict):
                            summary["last_message_role"] = last_message.get("role")
            
            if "session_id" in data:
                session_id = data["session_id"]
                if isinstance(session_id, str):
                    # 只记录会话ID的长度和格式，不记录实际值
                    summary["session_id_length"] = len(session_id)
                    summary["session_id_format"] = "uuid" if "-" in session_id else "custom"
            
            return summary
        
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "item_types": [type(item).__name__ for item in data[:3]]  # 只记录前3个元素的类型
            }
        
        elif isinstance(data, str):
            return {
                "type": "string",
                "length": len(data),
                "preview": data[:50] + "..." if len(data) > 50 else data
            }
        
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:50]
            }
    
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者名称
        """
        return "logging_observer"
    
    async def record_success(self, context: ValidationContext, execution_time: float) -> None:
        """记录成功事件
        
        Args:
            context: 验证上下文
            execution_time: 执行时间
        """
        if self.log_successful_validations:
            message = f"请求验证成功 - 路径: {context.request_path}"
            extra = {
                "request_id": context.request_id,
                "execution_time": execution_time,
                "user_id": context.user_id,
                "session_id": context.session_id
            }
            self._log("INFO", message, extra)
    
    async def record_error(self, path: str, error: str, execution_time: float) -> None:
        """记录错误事件
        
        Args:
            path: 请求路径
            error: 错误信息
            execution_time: 执行时间
        """
        message = f"请求处理错误 - 路径: {path}"
        extra = {
            "error": error[:self.max_content_length],
            "execution_time": execution_time
        }
        self._log("ERROR", message, extra)
