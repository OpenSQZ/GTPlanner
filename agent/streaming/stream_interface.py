"""
流式响应接口定义

定义流式响应系统的核心接口，支持不同类型的客户端（CLI、HTTP SSE等）。
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any, List
from .stream_types import StreamEvent, StreamEventIterator


class StreamHandler(ABC):
    """流式事件处理器抽象基类"""
    
    @abstractmethod
    async def handle_event(self, event: StreamEvent) -> None:
        """处理单个流式事件"""
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception, session_id: Optional[str] = None) -> None:
        """处理错误事件"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭处理器，清理资源"""
        pass


class StreamProducer(ABC):
    """流式事件生产者抽象基类"""
    
    @abstractmethod
    async def produce_events(
        self, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> StreamEventIterator:
        """生产流式事件序列"""
        pass
    
    @abstractmethod
    async def stop_production(self) -> None:
        """停止事件生产"""
        pass


class StreamConsumer(ABC):
    """流式事件消费者抽象基类"""
    
    @abstractmethod
    async def consume_events(self, event_stream: StreamEventIterator) -> None:
        """消费流式事件序列"""
        pass
    
    @abstractmethod
    async def stop_consumption(self) -> None:
        """停止事件消费"""
        pass


class StreamingSession:
    """流式会话管理器"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.is_active = False
        self.handlers: List[StreamHandler] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_handler(self, handler: StreamHandler) -> None:
        """添加事件处理器"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: StreamHandler) -> None:
        """移除事件处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    async def emit_event(self, event: StreamEvent) -> None:
        """向所有处理器发送事件"""
        event.session_id = self.session_id
        for handler in self.handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                # 处理器错误不应该影响其他处理器
                await handler.handle_error(e, self.session_id)
    
    async def start(self) -> None:
        """启动会话"""
        self.is_active = True
    
    async def stop(self) -> None:
        """停止会话"""
        self.is_active = False
        for handler in self.handlers:
            await handler.close()
        self.handlers.clear()


class StreamingManager:
    """流式响应管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, StreamingSession] = {}
    
    def create_session(self, session_id: str) -> StreamingSession:
        """创建新的流式会话"""
        if session_id in self.sessions:
            # 如果会话已存在，先清理旧会话
            old_session = self.sessions[session_id]
            if old_session.is_active:
                # 异步清理，不阻塞当前操作
                import asyncio
                asyncio.create_task(old_session.stop())
        
        session = StreamingSession(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """获取现有会话"""
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str) -> None:
        """关闭并清理会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.stop()
            del self.sessions[session_id]
    
    async def close_all_sessions(self) -> None:
        """关闭所有会话"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# 全局流式管理器实例
streaming_manager = StreamingManager()


class StreamingCapable(ABC):
    """支持流式响应的组件接口"""
    
    @abstractmethod
    async def process_with_streaming(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        session: StreamingSession
    ) -> Dict[str, Any]:
        """带流式响应的处理方法"""
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """是否支持流式响应"""
        pass


class StreamingResult:
    """流式处理结果"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[StreamEvent] = []
        self.final_result: Optional[Dict[str, Any]] = None
        self.error: Optional[Exception] = None
        self.is_complete = False
    
    def add_event(self, event: StreamEvent) -> None:
        """添加事件到结果中"""
        self.events.append(event)
    
    def set_final_result(self, result: Dict[str, Any]) -> None:
        """设置最终结果"""
        self.final_result = result
        self.is_complete = True
    
    def set_error(self, error: Exception) -> None:
        """设置错误"""
        self.error = error
        self.is_complete = True
    
    def get_assistant_messages(self) -> List[str]:
        """提取所有助手消息内容"""
        messages = []
        current_message = ""
        
        for event in self.events:
            if event.event_type.value == "assistant_message_chunk":
                current_message += event.data.get("content", "")
            elif event.event_type.value == "assistant_message_end":
                if current_message:
                    messages.append(current_message)
                    current_message = ""
                # 也可以从complete_message获取
                complete_msg = event.data.get("complete_message")
                if complete_msg and complete_msg not in messages:
                    messages.append(complete_msg)
        
        # 如果还有未完成的消息
        if current_message:
            messages.append(current_message)
        
        return messages
    
    def get_tool_executions(self) -> List[Dict[str, Any]]:
        """提取所有工具执行结果"""
        tool_executions = []
        
        for event in self.events:
            if event.event_type.value == "tool_call_end":
                tool_data = event.data
                if tool_data.get("status") == "completed":
                    tool_executions.append({
                        "tool_name": tool_data.get("tool_name"),
                        "arguments": tool_data.get("arguments", {}),
                        "result": tool_data.get("result", {}),
                        "execution_time": tool_data.get("execution_time"),
                        "timestamp": event.timestamp
                    })
        
        return tool_executions
