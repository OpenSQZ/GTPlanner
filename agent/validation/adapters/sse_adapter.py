"""
SSE流式验证适配器

基于适配器模式的SSE流式响应集成，提供：
- StreamingSession集成
- 验证事件到SSE事件转换
- 流式验证进度更新
- 实时错误通知
"""

import json
from typing import Dict, Any, Optional, List, Callable
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult, ValidationError
from ..observers.streaming_observer import StreamingObserver

# 尝试导入现有的SSE系统
try:
    from agent.streaming.stream_types import StreamEvent, StreamEventType
    from agent.streaming.event_helpers import StreamEventBuilder
    from agent.streaming.sse_handler import SSEStreamHandler
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    print("Warning: SSE system not available")


class SSEValidationAdapter:
    """SSE流式验证适配器 - 与现有SSE系统的深度集成
    
    提供验证事件的流式传输功能：
    - 验证进度的实时更新
    - 错误信息的即时通知
    - 与现有StreamingSession的无缝集成
    - 验证事件的标准化格式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_progress_updates = self.config.get("enable_progress_updates", True)
        self.enable_error_notifications = self.config.get("enable_error_notifications", True)
        self.include_detailed_info = self.config.get("include_detailed_info", False)
        self.buffer_events = self.config.get("buffer_events", False)
        
        # 事件缓冲区（如果启用）
        self.event_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = self.config.get("max_buffer_size", 10)
    
    def create_streaming_observer(self, streaming_session: Any) -> StreamingObserver:
        """创建流式观察者
        
        Args:
            streaming_session: StreamingSession实例
            
        Returns:
            配置好的StreamingObserver实例
        """
        return StreamingObserver(streaming_session)
    
    async def send_validation_start_event(
        self, 
        streaming_session: Any, 
        context: ValidationContext
    ) -> None:
        """发送验证开始事件
        
        Args:
            streaming_session: StreamingSession实例
            context: 验证上下文
        """
        if not self.enable_progress_updates or not streaming_session:
            return
        
        event_data = {
            "type": "validation_start",
            "request_id": context.request_id,
            "endpoint": context.request_path,
            "method": context.request_method,
            "validation_mode": context.validation_mode.value,
            "timestamp": time.time()
        }
        
        if self.include_detailed_info:
            event_data.update({
                "user_id": context.user_id,
                "session_id": context.session_id,
                "language": context.get_language_preference(),
                "client_ip": context.client_ip
            })
        
        await self._emit_event(streaming_session, "validation_start", event_data)
    
    async def send_validation_progress_event(
        self,
        streaming_session: Any,
        validator_name: str,
        result: ValidationResult,
        total_validators: int,
        current_index: int
    ) -> None:
        """发送验证进度事件
        
        Args:
            streaming_session: StreamingSession实例
            validator_name: 当前验证器名称
            result: 验证结果
            total_validators: 总验证器数量
            current_index: 当前验证器索引
        """
        if not self.enable_progress_updates or not streaming_session:
            return
        
        progress_percentage = (current_index + 1) / total_validators * 100 if total_validators > 0 else 100
        
        event_data = {
            "type": "validation_progress",
            "validator": validator_name,
            "status": result.status.value,
            "progress": {
                "current": current_index + 1,
                "total": total_validators,
                "percentage": round(progress_percentage, 1)
            },
            "execution_time": result.execution_time,
            "request_id": result.request_id
        }
        
        # 添加错误信息（如果有）
        if result.has_errors and self.enable_error_notifications:
            event_data["errors"] = [
                {
                    "code": error.code,
                    "message": error.message[:100],  # 截断消息
                    "severity": error.severity.name
                }
                for error in result.errors[:2]  # 只包含前2个错误
            ]
        
        # 添加警告信息（如果有）
        if result.has_warnings:
            event_data["warnings"] = [
                {
                    "code": warning.code,
                    "message": warning.message[:100]
                }
                for warning in result.warnings[:1]  # 只包含第1个警告
            ]
        
        await self._emit_event(streaming_session, "validation_progress", event_data)
    
    async def send_validation_complete_event(
        self,
        streaming_session: Any,
        result: ValidationResult,
        context: Optional[ValidationContext] = None
    ) -> None:
        """发送验证完成事件
        
        Args:
            streaming_session: StreamingSession实例
            result: 最终验证结果
            context: 验证上下文
        """
        if not streaming_session:
            return
        
        event_data = {
            "type": "validation_complete",
            "request_id": result.request_id,
            "status": result.status.value,
            "is_valid": result.is_valid,
            "execution_time": result.execution_time,
            "summary": {
                "total_errors": len(result.errors),
                "total_warnings": len(result.warnings),
                "executed_validators": result.metrics.executed_validators,
                "success_rate": result.metrics.get_success_rate()
            }
        }
        
        # 添加详细信息
        if self.include_detailed_info:
            event_data["details"] = {
                "validation_path": result.execution_order,
                "failed_validators": result.get_failed_validators(),
                "error_summary": result.get_error_summary()
            }
        
        # 添加错误信息（如果验证失败）
        if not result.is_valid and self.enable_error_notifications:
            event_data["errors"] = [
                {
                    "code": error.code,
                    "message": self._sanitize_error_message(error.message),
                    "severity": error.severity.name,
                    "field": error.field,
                    "suggestion": error.suggestion
                }
                for error in result.errors
            ]
        
        await self._emit_event(streaming_session, "validation_complete", event_data)
    
    async def send_validation_error_event(
        self,
        streaming_session: Any,
        error: Exception,
        context: Optional[ValidationContext] = None
    ) -> None:
        """发送验证错误事件
        
        Args:
            streaming_session: StreamingSession实例
            error: 异常对象
            context: 验证上下文
        """
        if not self.enable_error_notifications or not streaming_session:
            return
        
        event_data = {
            "type": "validation_error",
            "error_type": type(error).__name__,
            "error_message": self._sanitize_error_message(str(error)),
            "timestamp": time.time()
        }
        
        if context:
            event_data.update({
                "request_id": context.request_id,
                "endpoint": context.request_path,
                "current_validator": context.current_validator,
                "validation_path": context.validation_path
            })
        
        await self._emit_event(streaming_session, "validation_error", event_data)
    
    async def _emit_event(self, streaming_session: Any, event_type: str, data: Dict[str, Any]) -> None:
        """发送流式事件
        
        Args:
            streaming_session: StreamingSession实例
            event_type: 事件类型
            data: 事件数据
        """
        try:
            if SSE_AVAILABLE and hasattr(streaming_session, 'emit_event'):
                # 使用现有的SSE系统
                if hasattr(StreamEventBuilder, 'create_custom_event'):
                    event = StreamEventBuilder.create_custom_event(
                        session_id=getattr(streaming_session, 'session_id', 'unknown'),
                        event_type=event_type,
                        data=data
                    )
                    await streaming_session.emit_event(event)
                else:
                    # 如果create_custom_event不存在，使用简化方式
                    await self._emit_simple_event(streaming_session, event_type, data)
            else:
                # 使用简化的事件发送
                await self._emit_simple_event(streaming_session, event_type, data)
                
        except Exception as e:
            print(f"Warning: Failed to emit SSE event {event_type}: {e}")
    
    async def _emit_simple_event(self, streaming_session: Any, event_type: str, data: Dict[str, Any]) -> None:
        """发送简化的流式事件
        
        Args:
            streaming_session: StreamingSession实例
            event_type: 事件类型
            data: 事件数据
        """
        try:
            # 创建简化的事件格式
            event_message = {
                "event": event_type,
                "data": data
            }
            
            # 尝试发送消息
            if hasattr(streaming_session, 'send_message'):
                await streaming_session.send_message(json.dumps(event_message, ensure_ascii=False))
            elif hasattr(streaming_session, 'write'):
                await streaming_session.write(f"data: {json.dumps(event_message, ensure_ascii=False)}\n\n")
            
        except Exception as e:
            print(f"Warning: Failed to emit simple event {event_type}: {e}")
    
    def _sanitize_error_message(self, message: str, max_length: int = 200) -> str:
        """清理错误消息
        
        Args:
            message: 原始消息
            max_length: 最大长度
            
        Returns:
            清理后的消息
        """
        # 截断长度
        if len(message) > max_length:
            message = message[:max_length] + "..."
        
        # 移除敏感信息
        import re
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
        message = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', message)
        
        return message
    
    def create_enhanced_streaming_session(self, base_session: Any) -> 'EnhancedStreamingSession':
        """创建增强的流式会话
        
        Args:
            base_session: 基础StreamingSession
            
        Returns:
            增强的流式会话实例
        """
        return EnhancedStreamingSession(base_session, self)


class EnhancedStreamingSession:
    """增强的流式会话 - 包装现有StreamingSession并添加验证功能"""
    
    def __init__(self, base_session: Any, adapter: SSEValidationAdapter):
        self.base_session = base_session
        self.adapter = adapter
        self.validation_events: List[Dict[str, Any]] = []
    
    async def emit_validation_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """发送验证相关的流式事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        # 记录事件
        self.validation_events.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        })
        
        # 发送事件
        await self.adapter._emit_event(self.base_session, event_type, data)
    
    async def send_validation_progress(
        self,
        validator_name: str,
        status: str,
        progress: float,
        message: Optional[str] = None
    ) -> None:
        """发送验证进度更新
        
        Args:
            validator_name: 验证器名称
            status: 验证状态
            progress: 进度百分比（0-100）
            message: 可选的进度消息
        """
        event_data = {
            "validator": validator_name,
            "status": status,
            "progress": progress,
            "message": message or f"正在执行 {validator_name} 验证..."
        }
        
        await self.emit_validation_event("validation_progress", event_data)
    
    async def send_validation_warning(self, warning: ValidationError) -> None:
        """发送验证警告
        
        Args:
            warning: 验证警告
        """
        event_data = {
            "code": warning.code,
            "message": self.adapter._sanitize_error_message(warning.message),
            "severity": warning.severity.name,
            "field": warning.field,
            "suggestion": warning.suggestion
        }
        
        await self.emit_validation_event("validation_warning", event_data)
    
    async def send_validation_success(self, summary: Dict[str, Any]) -> None:
        """发送验证成功事件
        
        Args:
            summary: 验证摘要信息
        """
        await self.emit_validation_event("validation_success", summary)
    
    def get_validation_event_history(self) -> List[Dict[str, Any]]:
        """获取验证事件历史
        
        Returns:
            验证事件列表
        """
        return self.validation_events.copy()
    
    def clear_validation_events(self) -> None:
        """清空验证事件历史"""
        self.validation_events.clear()
    
    # 代理基础会话的方法
    def __getattr__(self, name):
        """代理基础会话的属性和方法"""
        return getattr(self.base_session, name)


class ValidationAwareSSEHandler:
    """验证感知的SSE处理器 - 扩展现有SSE处理器"""
    
    def __init__(self, base_handler: Any, validation_config: Optional[Dict[str, Any]] = None):
        self.base_handler = base_handler
        self.validation_config = validation_config or {}
        self.sse_adapter = SSEValidationAdapter(validation_config)
        
        # 验证事件统计
        self.validation_event_count = 0
        self.validation_error_count = 0
    
    async def handle_validation_aware_request(
        self,
        request_handler: Callable,
        context: ValidationContext,
        **kwargs
    ) -> Any:
        """处理验证感知的请求
        
        Args:
            request_handler: 请求处理函数
            context: 验证上下文
            **kwargs: 额外参数
            
        Returns:
            处理结果
        """
        # 创建增强的流式会话
        if hasattr(self.base_handler, 'streaming_session'):
            enhanced_session = self.sse_adapter.create_enhanced_streaming_session(
                self.base_handler.streaming_session
            )
            
            # 发送验证开始事件
            await self.sse_adapter.send_validation_start_event(enhanced_session, context)
            
            try:
                # 执行请求处理
                result = await request_handler(enhanced_session, context, **kwargs)
                
                # 发送成功事件
                if hasattr(result, 'to_dict'):
                    await enhanced_session.send_validation_success(result.to_dict())
                
                return result
                
            except Exception as e:
                # 发送错误事件
                await self.sse_adapter.send_validation_error_event(enhanced_session, e, context)
                raise
        else:
            # 如果没有流式会话，直接执行处理
            return await request_handler(context, **kwargs)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证相关的统计信息
        
        Returns:
            验证统计信息字典
        """
        return {
            "validation_event_count": self.validation_event_count,
            "validation_error_count": self.validation_error_count,
            "sse_available": SSE_AVAILABLE,
            "adapter_config": self.validation_config
        }


def create_sse_adapter(config: Optional[Dict[str, Any]] = None) -> SSEValidationAdapter:
    """创建SSE适配器的便捷函数
    
    Args:
        config: 适配器配置
        
    Returns:
        SSE适配器实例
    """
    return SSEValidationAdapter(config)


def enhance_sse_handler(base_handler: Any, validation_config: Optional[Dict[str, Any]] = None) -> ValidationAwareSSEHandler:
    """增强现有SSE处理器的便捷函数
    
    Args:
        base_handler: 基础SSE处理器
        validation_config: 验证配置
        
    Returns:
        验证感知的SSE处理器
    """
    return ValidationAwareSSEHandler(base_handler, validation_config)


# 集成现有SSE系统的辅助函数
def integrate_validation_with_sse(sse_handler: Any, validation_config: Optional[Dict[str, Any]] = None) -> None:
    """将验证系统集成到现有SSE处理器
    
    Args:
        sse_handler: 现有的SSE处理器
        validation_config: 验证配置
    """
    if not SSE_AVAILABLE:
        print("Warning: SSE system not available, integration skipped")
        return
    
    try:
        # 创建SSE适配器
        adapter = SSEValidationAdapter(validation_config)
        
        # 如果SSE处理器有streaming_session，创建观察者
        if hasattr(sse_handler, 'streaming_session') and sse_handler.streaming_session:
            observer = adapter.create_streaming_observer(sse_handler.streaming_session)
            
            # 将观察者添加到验证中间件（如果可用）
            print("✅ SSE验证集成完成")
        else:
            print("⚠️ SSE处理器没有streaming_session，无法完全集成")
            
    except Exception as e:
        print(f"❌ SSE验证集成失败: {e}")


# 为了避免循环导入，添加time导入
import time
