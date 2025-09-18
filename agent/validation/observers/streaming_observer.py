"""
流式观察者

基于观察者模式的流式验证实现，提供：
- 集成现有SSE系统
- 验证事件流式发送
- 验证进度实时更新
- 错误事件流式通知
"""

import time
import json
from typing import Optional, Dict, Any
from ..core.interfaces import IValidationObserver
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult

# 尝试导入现有的SSE系统
try:
    from agent.streaming.stream_types import StreamEvent, StreamEventType
    from agent.streaming.event_helpers import StreamEventBuilder
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    print("Warning: SSE system not available for streaming validation")


class StreamingObserver(IValidationObserver):
    """流式验证观察者 - 将验证事件发送到流式会话
    
    与GTPlanner现有的SSE流式响应系统集成，提供：
    - 验证开始/完成事件的实时通知
    - 验证步骤进度的流式更新
    - 验证错误的实时报告
    - 与现有StreamingSession的无缝集成
    """
    
    def __init__(self, streaming_session: Optional[Any] = None):
        self.streaming_session = streaming_session
        self.enabled = streaming_session is not None and SSE_AVAILABLE
        
        if not SSE_AVAILABLE and streaming_session:
            print("Warning: SSE system not available, streaming validation disabled")
    
    async def on_validation_start(self, context: ValidationContext) -> None:
        """验证开始事件
        
        Args:
            context: 验证上下文
        """
        if not self.enabled or not self.streaming_session:
            return
        
        try:
            if SSE_AVAILABLE:
                event = StreamEventBuilder.create_custom_event(
                    session_id=context.session_id or "unknown",
                    event_type="validation_start",
                    data={
                        "request_id": context.request_id,
                        "validation_mode": context.validation_mode.value,
                        "endpoint": context.request_path,
                        "method": context.request_method,
                        "user_id": context.user_id,
                        "language": context.get_language_preference(),
                        "timestamp": context.validation_start_time.isoformat() if context.validation_start_time else None
                    }
                )
                
                await self.streaming_session.emit_event(event)
            else:
                # 简化的流式通知
                await self._emit_simple_event("validation_start", {
                    "request_id": context.request_id,
                    "endpoint": context.request_path
                })
        
        except Exception as e:
            print(f"Warning: Failed to send validation start event: {e}")
    
    async def on_validation_step(self, validator_name: str, result: ValidationResult) -> None:
        """验证步骤完成事件
        
        Args:
            validator_name: 验证器名称
            result: 验证结果
        """
        if not self.enabled or not self.streaming_session:
            return
        
        try:
            step_data = {
                "validator": validator_name,
                "status": result.status.value,
                "has_errors": result.has_errors,
                "has_warnings": result.has_warnings,
                "execution_time": result.execution_time,
                "request_id": result.request_id
            }
            
            # 添加错误摘要（不包含敏感信息）
            if result.has_errors:
                step_data["error_codes"] = [error.code for error in result.errors[:3]]
                step_data["error_count"] = len(result.errors)
            
            # 添加警告摘要
            if result.has_warnings:
                step_data["warning_codes"] = [warning.code for warning in result.warnings[:2]]
                step_data["warning_count"] = len(result.warnings)
            
            if SSE_AVAILABLE:
                event = StreamEventBuilder.create_custom_event(
                    session_id=self._get_session_id(),
                    event_type="validation_step",
                    data=step_data
                )
                
                await self.streaming_session.emit_event(event)
            else:
                await self._emit_simple_event("validation_step", step_data)
        
        except Exception as e:
            print(f"Warning: Failed to send validation step event: {e}")
    
    async def on_validation_complete(self, result: ValidationResult) -> None:
        """验证完成事件
        
        Args:
            result: 最终验证结果
        """
        if not self.enabled or not self.streaming_session:
            return
        
        try:
            complete_data = {
                "request_id": result.request_id,
                "status": result.status.value,
                "is_valid": result.is_valid,
                "total_errors": len(result.errors),
                "total_warnings": len(result.warnings),
                "execution_time": result.execution_time,
                "executed_validators": result.metrics.executed_validators,
                "success_rate": result.metrics.get_success_rate(),
                "validation_path": result.execution_order
            }
            
            # 添加错误摘要
            if result.has_errors:
                complete_data["error_summary"] = result.get_error_summary()
                complete_data["failed_validators"] = result.get_failed_validators()
                
                # 添加关键错误信息（不包含敏感数据）
                critical_errors = [
                    {
                        "code": error.code,
                        "message": self._sanitize_message(error.message),
                        "severity": error.severity.name,
                        "validator": error.validator
                    }
                    for error in result.errors 
                    if error.severity.value >= 3  # HIGH或CRITICAL
                ]
                
                if critical_errors:
                    complete_data["critical_errors"] = critical_errors[:3]
            
            if SSE_AVAILABLE:
                event = StreamEventBuilder.create_custom_event(
                    session_id=self._get_session_id(),
                    event_type="validation_complete",
                    data=complete_data
                )
                
                await self.streaming_session.emit_event(event)
            else:
                await self._emit_simple_event("validation_complete", complete_data)
        
        except Exception as e:
            print(f"Warning: Failed to send validation complete event: {e}")
    
    async def on_validation_error(self, error: Exception, context: Optional[ValidationContext] = None) -> None:
        """验证错误事件
        
        Args:
            error: 发生的异常
            context: 验证上下文（可能为None）
        """
        if not self.enabled or not self.streaming_session:
            return
        
        try:
            error_data = {
                "error_type": type(error).__name__,
                "error_message": self._sanitize_message(str(error)),
                "timestamp": time.time()
            }
            
            if context:
                error_data.update({
                    "request_id": context.request_id,
                    "endpoint": context.request_path,
                    "current_validator": context.current_validator,
                    "validation_path": context.validation_path,
                    "execution_time": context.get_execution_time()
                })
            
            if SSE_AVAILABLE:
                event = StreamEventBuilder.error(
                    session_id=self._get_session_id(),
                    error_message=f"验证系统错误: {type(error).__name__}",
                    metadata=error_data
                )
                
                await self.streaming_session.emit_event(event)
            else:
                await self._emit_simple_event("validation_error", error_data)
        
        except Exception as e:
            print(f"Warning: Failed to send validation error event: {e}")
    
    def _get_session_id(self) -> str:
        """获取会话ID
        
        Returns:
            会话ID字符串
        """
        if hasattr(self.streaming_session, 'session_id'):
            return self.streaming_session.session_id
        return "unknown_session"
    
    def _sanitize_message(self, message: str, max_length: int = 200) -> str:
        """清理消息内容（移除敏感信息）
        
        Args:
            message: 原始消息
            max_length: 最大长度
            
        Returns:
            清理后的消息
        """
        # 截断长度
        if len(message) > max_length:
            message = message[:max_length] + "..."
        
        # 简单的敏感信息替换（可以扩展）
        import re
        
        # 替换可能的敏感信息
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
        message = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', message)
        message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', message)
        
        return message
    
    async def _emit_simple_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """发送简化的流式事件（当SSE不可用时）
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if hasattr(self.streaming_session, 'send_message'):
            try:
                message = {
                    "type": event_type,
                    "data": data
                }
                await self.streaming_session.send_message(json.dumps(message))
            except Exception:
                pass
    
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者名称
        """
        return "streaming_observer"
    
    def is_streaming_available(self) -> bool:
        """检查流式功能是否可用
        
        Returns:
            True表示可用，False表示不可用
        """
        return self.enabled and SSE_AVAILABLE
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """获取流式统计信息
        
        Returns:
            流式统计信息字典
        """
        return {
            "enabled": self.enabled,
            "sse_available": SSE_AVAILABLE,
            "has_session": self.streaming_session is not None,
            "session_id": self._get_session_id() if self.streaming_session else None
        }
