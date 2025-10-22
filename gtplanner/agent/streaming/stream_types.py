"""
流式响应数据类型定义

定义流式响应系统的核心数据结构和协议，支持CLI和HTTP SSE客户端。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, AsyncIterator, Callable
from enum import Enum
import json
from datetime import datetime


class StreamEventType(Enum):
    """流式事件类型"""
    # 对话相关事件
    CONVERSATION_START = "conversation_start"
    ASSISTANT_MESSAGE_START = "assistant_message_start"
    ASSISTANT_MESSAGE_CHUNK = "assistant_message_chunk"
    ASSISTANT_MESSAGE_END = "assistant_message_end"

    # 工具调用相关事件
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_PROGRESS = "tool_call_progress"
    TOOL_CALL_END = "tool_call_end"

    # 设计文档相关事件
    DESIGN_DOCUMENT_GENERATED = "design_document_generated"

    # 状态相关事件
    PROCESSING_STATUS = "processing_status"
    ERROR = "error"
    CONVERSATION_END = "conversation_end"


class StreamCallbackType(Enum):
    """流式回调类型（用于streaming_callbacks字典的键名）"""
    # LLM相关回调
    ON_LLM_START = "on_llm_start"
    ON_LLM_CHUNK = "on_llm_chunk"
    ON_LLM_END = "on_llm_end"

    # 工具调用相关回调
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_PROGRESS = "on_tool_progress"
    ON_TOOL_END = "on_tool_end"

    # 状态相关回调
    ON_PROCESSING_STATUS = "on_processing_status"
    ON_ERROR = "on_error"


@dataclass
class StreamEvent:
    """流式事件基础数据结构"""
    event_type: StreamEventType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "data": self.data,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def to_sse_format(self) -> str:
        """转换为Server-Sent Events格式"""
        return f"event: {self.event_type.value}\ndata: {self.to_json()}\n\n"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamEvent':
        """从字典创建StreamEvent实例"""
        return cls(
            event_type=StreamEventType(data["event_type"]),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            session_id=data.get("session_id"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class AssistantMessageChunk:
    """助手消息片段"""
    content: str
    is_complete: bool = False
    chunk_index: int = 0
    total_chunks: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "is_complete": self.is_complete,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks
        }


@dataclass
class ToolCallStatus:
    """工具调用状态"""
    tool_name: str
    status: str  # "starting", "running", "completed", "failed"
    call_id: Optional[str] = None  # 唯一的工具调用ID
    progress_message: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "call_id": self.call_id,
            "progress_message": self.progress_message,
            "arguments": self.arguments,
            "result": self.result,
            "execution_time": self.execution_time,
            "error_message": self.error_message
        }


@dataclass
class DesignDocument:
    """设计文档数据结构"""
    filename: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "content": self.content
        }


class StreamEventBuilder:
    """流式事件构建器"""
    
    @staticmethod
    def conversation_start(session_id: str, user_input: str) -> StreamEvent:
        """创建对话开始事件"""
        return StreamEvent(
            event_type=StreamEventType.CONVERSATION_START,
            session_id=session_id,
            data={"user_input": user_input}
        )
    
    @staticmethod
    def assistant_message_start(session_id: str) -> StreamEvent:
        """创建助手消息开始事件"""
        return StreamEvent(
            event_type=StreamEventType.ASSISTANT_MESSAGE_START,
            session_id=session_id,
            data={}
        )
    
    @staticmethod
    def assistant_message_chunk(
        session_id: str, 
        chunk: AssistantMessageChunk
    ) -> StreamEvent:
        """创建助手消息片段事件"""
        return StreamEvent(
            event_type=StreamEventType.ASSISTANT_MESSAGE_CHUNK,
            session_id=session_id,
            data=chunk.to_dict()
        )
    
    @staticmethod
    def assistant_message_end(
        session_id: str, 
        complete_message: str,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> StreamEvent:
        """创建助手消息结束事件"""
        return StreamEvent(
            event_type=StreamEventType.ASSISTANT_MESSAGE_END,
            session_id=session_id,
            data={
                "complete_message": complete_message,
                "message_metadata": message_metadata or {}
            }
        )
    
    @staticmethod
    def tool_call_start(
        session_id: str, 
        tool_status: ToolCallStatus
    ) -> StreamEvent:
        """创建工具调用开始事件"""
        return StreamEvent(
            event_type=StreamEventType.TOOL_CALL_START,
            session_id=session_id,
            data=tool_status.to_dict()
        )
    
    @staticmethod
    def tool_call_progress(
        session_id: str, 
        tool_status: ToolCallStatus
    ) -> StreamEvent:
        """创建工具调用进度事件"""
        return StreamEvent(
            event_type=StreamEventType.TOOL_CALL_PROGRESS,
            session_id=session_id,
            data=tool_status.to_dict()
        )
    
    @staticmethod
    def tool_call_end(
        session_id: str, 
        tool_status: ToolCallStatus
    ) -> StreamEvent:
        """创建工具调用结束事件"""
        return StreamEvent(
            event_type=StreamEventType.TOOL_CALL_END,
            session_id=session_id,
            data=tool_status.to_dict()
        )
    
    @staticmethod
    def processing_status(
        session_id: str, 
        status_message: str,
        progress_info: Optional[Dict[str, Any]] = None
    ) -> StreamEvent:
        """创建处理状态事件"""
        return StreamEvent(
            event_type=StreamEventType.PROCESSING_STATUS,
            session_id=session_id,
            data={
                "status_message": status_message,
                "progress_info": progress_info or {}
            }
        )
    
    @staticmethod
    def error(
        session_id: str, 
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> StreamEvent:
        """创建错误事件"""
        return StreamEvent(
            event_type=StreamEventType.ERROR,
            session_id=session_id,
            data={
                "error_message": error_message,
                "error_details": error_details or {}
            }
        )
    
    @staticmethod
    def conversation_end(
        session_id: str,
        final_result: Dict[str, Any],
        tool_execution_results_updates: Optional[Dict[str, Any]] = None
    ) -> StreamEvent:
        """创建对话结束事件"""
        data = final_result.copy()
        if tool_execution_results_updates:
            data["tool_execution_results_updates"] = tool_execution_results_updates

        return StreamEvent(
            event_type=StreamEventType.CONVERSATION_END,
            session_id=session_id,
            data=data
        )

    @staticmethod
    def design_document_generated(
        session_id: str,
        document: DesignDocument
    ) -> StreamEvent:
        """创建设计文档生成事件"""
        return StreamEvent(
            event_type=StreamEventType.DESIGN_DOCUMENT_GENERATED,
            session_id=session_id,
            data=document.to_dict()
        )


# 类型别名
StreamEventIterator = AsyncIterator[StreamEvent]
StreamEventHandler = Callable[[StreamEvent], None]
