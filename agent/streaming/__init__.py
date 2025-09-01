"""
流式响应系统

提供完整的流式响应功能，支持CLI和HTTP SSE客户端。
"""

from .stream_types import (
    StreamEvent,
    StreamEventType,
    StreamCallbackType,
    StreamEventBuilder,
    AssistantMessageChunk,
    ToolCallStatus,
    DesignDocument,
    StreamEventIterator,
    StreamEventHandler
)

from .stream_interface import (
    StreamHandler,
    StreamProducer,
    StreamConsumer,
    StreamingSession,
    StreamingManager,
    StreamingCapable,
    StreamingResult,
    streaming_manager
)

from .cli_handler import CLIStreamHandler

from .event_helpers import (
    emit_processing_status,
    emit_error,
    emit_tool_start,
    emit_tool_progress,
    emit_tool_end,
    emit_processing_status_from_prep,
    emit_error_from_prep,
    emit_event_auto,
    emit_design_document
)

__all__ = [
    # 核心类型
    "StreamEvent",
    "StreamEventType",
    "StreamCallbackType",
    "StreamEventBuilder",
    "AssistantMessageChunk",
    "ToolCallStatus",
    "DesignDocument",
    "StreamEventIterator",
    "StreamEventHandler",

    # 接口和管理
    "StreamHandler",
    "StreamProducer",
    "StreamConsumer",
    "StreamingSession",
    "StreamingManager",
    "StreamingCapable",
    "StreamingResult",
    "streaming_manager",

    # 具体实现
    "CLIStreamHandler",

    # 辅助函数
    "emit_processing_status",
    "emit_error",
    "emit_tool_start",
    "emit_tool_progress",
    "emit_tool_end",
    "emit_processing_status_from_prep",
    "emit_error_from_prep",
    "emit_event_auto",
    "emit_design_document"
]
