"""
SSE流式处理器

为HTTP Server-Sent Events客户端提供流式响应处理，支持实时传输LLM回复和工具调用状态。

使用示例:
    ```python
    import asyncio
    from gtplanner.agent.streaming.sse_handler import SSEStreamHandler
    from gtplanner.agent.streaming.stream_types import StreamEvent, StreamEventType

    # 定义SSE写入函数
    async def write_sse_data(data: str):
        # 这里应该写入到HTTP响应流
        print(f"SSE: {data}", end="")

    # 创建SSE处理器
    handler = SSEStreamHandler(
        response_writer=write_sse_data,
        include_metadata=True,
        buffer_events=False,
        heartbeat_interval=30.0
    )

    # 处理事件
    event = StreamEvent(
        event_type=StreamEventType.ASSISTANT_MESSAGE_CHUNK,
        data={"content": "Hello, world!"}
    )
    await handler.handle_event(event)

    # 关闭处理器
    await handler.close()
    ```
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

from .stream_types import StreamEvent, StreamEventType
from .stream_interface import StreamHandler


logger = logging.getLogger(__name__)


class SSEStreamHandler(StreamHandler):
    """
    SSE流式事件处理器
    负责将流式事件转换为Server-Sent Events格式，包括：
    - 实时传输LLM回复内容
    - 传输工具调用状态和进度
    - 优雅处理错误和连接中断
    - 支持心跳机制保持连接活跃
    """

    def __init__(
        self, 
        response_writer: Callable[[str], Awaitable[None]],
        include_metadata: bool = False,
        buffer_events: bool = False,
        heartbeat_interval: float = 30.0
    ):
        """
        初始化SSE处理器
        
        Args:
            response_writer: 用于写入SSE数据的异步回调函数
            include_metadata: 是否包含详细元数据
            buffer_events: 是否缓冲事件以优化传输
            heartbeat_interval: 心跳间隔（秒）
        """
        self.response_writer = response_writer
        self.include_metadata = include_metadata
        self.buffer_events = buffer_events
        self.heartbeat_interval = heartbeat_interval
        
        # 状态管理
        self._closed = False
        self._message_buffer = ""
        self._is_message_active = False
        self.active_tools: Dict[str, Dict[str, Any]] = {}
        self._last_heartbeat = datetime.now()
        self._event_buffer = []
        
        # 启动心跳任务
        self._heartbeat_task = None
        if heartbeat_interval > 0:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def handle_event(self, event: StreamEvent) -> None:
        """处理单个流式事件"""
        if self._closed:
            return

        try:
            if event.event_type == StreamEventType.CONVERSATION_START:
                await self._handle_conversation_start(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_START:
                await self._handle_message_start(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_CHUNK:
                await self._handle_message_chunk(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_END:
                await self._handle_message_end(event)

            elif event.event_type == StreamEventType.TOOL_CALL_START:
                await self._handle_tool_start(event)

            elif event.event_type == StreamEventType.TOOL_CALL_PROGRESS:
                await self._handle_tool_progress(event)

            elif event.event_type == StreamEventType.TOOL_CALL_END:
                await self._handle_tool_end(event)

            elif event.event_type == StreamEventType.PROCESSING_STATUS:
                await self._handle_processing_status(event)

            elif event.event_type == StreamEventType.ERROR:
                await self._handle_error_event(event)

            elif event.event_type == StreamEventType.DESIGN_DOCUMENT_GENERATED:
                await self._handle_design_document(event)

            elif event.event_type == StreamEventType.PREFABS_INFO:
                await self._handle_prefabs_info(event)

            elif event.event_type == StreamEventType.DOCUMENT_EDIT_PROPOSAL:
                await self._handle_document_edit_proposal(event)

            elif event.event_type == StreamEventType.CONVERSATION_END:
                await self._handle_conversation_end(event)

        except Exception as e:
            await self.handle_error(e, event.session_id)

    async def _handle_conversation_start(self, event: StreamEvent) -> None:
        """处理对话开始事件"""
        # 发送原始事件
        await self._write_sse_event(event)
        
        # 发送状态更新
        await self._send_status_update(
            "conversation_started",
            {
                "user_input": event.data.get("user_input", ""),
                "timestamp": event.timestamp
            }
        )

    async def _handle_message_start(self, event: StreamEvent) -> None:
        """处理助手消息开始事件"""
        self._is_message_active = True
        self._message_buffer = ""
        
        # 发送消息开始事件
        await self._write_sse_event(event)

    async def _handle_message_chunk(self, event: StreamEvent) -> None:
        """处理助手消息片段事件"""
        chunk_content = event.data.get("content", "")
        
        if chunk_content:
            self._message_buffer += chunk_content
            
            if self.buffer_events:
                # 缓冲事件
                self._event_buffer.append(event)
                # 如果缓冲区达到一定大小，刷新
                if len(self._event_buffer) >= 5:
                    await self._flush_buffer()
            else:
                # 立即发送
                await self._write_sse_event(event)

    async def _handle_message_end(self, event: StreamEvent) -> None:
        """处理助手消息结束事件"""
        if self._is_message_active:
            # 刷新任何缓冲的事件
            await self._flush_buffer()
            
            # 发送消息结束事件
            await self._write_sse_event(event)
            
            self._is_message_active = False
            self._message_buffer = ""

    async def _handle_tool_start(self, event: StreamEvent) -> None:
        """处理工具调用开始事件"""
        tool_name = event.data.get("tool_name", "unknown")
        
        # 记录活跃工具
        self.active_tools[tool_name] = {
            "start_time": datetime.now(),
            "status": "running"
        }
        
        # 立即发送工具开始事件
        await self._write_sse_event(event)

    async def _handle_tool_progress(self, event: StreamEvent) -> None:
        """处理工具调用进度事件"""
        # 立即发送进度事件
        await self._write_sse_event(event)

    async def _handle_tool_end(self, event: StreamEvent) -> None:
        """处理工具调用结束事件"""
        tool_name = event.data.get("tool_name", "unknown")
        
        # 移除活跃工具记录
        if tool_name in self.active_tools:
            del self.active_tools[tool_name]
        
        # 立即发送工具结束事件
        await self._write_sse_event(event)

    async def _handle_processing_status(self, event: StreamEvent) -> None:
        """处理处理状态事件"""
        # 立即发送状态事件
        await self._write_sse_event(event)

    async def _handle_error_event(self, event: StreamEvent) -> None:
        """处理错误事件"""
        # 刷新缓冲区
        await self._flush_buffer()

        # 立即发送错误事件
        await self._write_sse_event(event)

    async def _handle_design_document(self, event: StreamEvent) -> None:
        """处理设计文档生成事件"""
        # 刷新缓冲区以确保之前的消息都已发送
        await self._flush_buffer()

        # 直接发送设计文档事件
        await self._write_sse_event(event)

        # 如果启用了元数据，发送额外的状态信息
        if self.include_metadata:
            filename = event.data.get("filename", "unknown.md")
            content_length = len(event.data.get("content", ""))

            await self._send_status_update(
                "design_document_generated",
                {
                    "filename": filename,
                    "content_length": content_length,
                    "timestamp": event.timestamp
                }
            )

    async def _handle_prefabs_info(self, event: StreamEvent) -> None:
        """处理预制件信息事件"""
        logger.info(f"📦 [SSE Handler] 处理 prefabs_info 事件，包含 {len(event.data.get('prefabs', []))} 个预制件")
        
        # 刷新缓冲区以确保之前的消息都已发送
        await self._flush_buffer()

        # 直接发送预制件信息事件
        await self._write_sse_event(event)
        logger.info(f"✅ [SSE Handler] prefabs_info 事件已发送到前端")

        # 如果启用了元数据，发送额外的状态信息
        if self.include_metadata:
            prefabs_count = len(event.data.get("prefabs", []))

            await self._send_status_update(
                "prefabs_info_sent",
                {
                    "prefabs_count": prefabs_count,
                    "timestamp": event.timestamp
                }
            )

    async def _handle_document_edit_proposal(self, event: StreamEvent) -> None:
        """处理文档编辑提案事件"""
        proposal_id = event.data.get("proposal_id", "unknown")
        edits_count = len(event.data.get("edits", []))
        logger.info(f"📝 [SSE Handler] 处理 document_edit_proposal 事件 (ID: {proposal_id}, {edits_count} 个编辑)")
        
        # 刷新缓冲区以确保之前的消息都已发送
        await self._flush_buffer()

        # 直接发送文档编辑提案事件
        await self._write_sse_event(event)
        logger.info(f"✅ [SSE Handler] document_edit_proposal 事件已发送到前端 (ID: {proposal_id})")

        # 如果启用了元数据，发送额外的状态信息
        if self.include_metadata:
            await self._send_status_update(
                "document_edit_proposal_sent",
                {
                    "proposal_id": proposal_id,
                    "edits_count": edits_count,
                    "document_type": event.data.get("document_type"),
                    "timestamp": event.timestamp
                }
            )

    async def _handle_conversation_end(self, event: StreamEvent) -> None:
        """处理对话结束事件"""
        # 刷新所有缓冲
        await self._flush_buffer()

        # 发送对话结束事件
        await self._write_sse_event(event)

        # 发送最终状态
        await self._send_status_update(
            "conversation_ended",
            {
                "success": event.data.get("success", False),
                "execution_time": event.data.get("execution_time", 0),
                "timestamp": event.timestamp
            }
        )

        # 标记会话结束，但不自动关闭（由上层控制关闭时机）
        logger.info(f"对话结束 (会话: {event.session_id})")

    async def handle_error(self, error: Exception, session_id: Optional[str] = None) -> None:
        """处理错误"""
        if self._closed:
            return

        logger.error(f"SSE处理器错误: {error}", exc_info=True)
        
        # 创建错误事件
        error_event = StreamEvent(
            event_type=StreamEventType.ERROR,
            session_id=session_id,
            data={
                "error_message": str(error),
                "error_type": type(error).__name__,
                "error_details": {"session_id": session_id} if self.include_metadata else {}
            }
        )
        
        try:
            await self._write_sse_event(error_event)
        except Exception as write_error:
            logger.error(f"无法发送错误事件: {write_error}")

        # 错误处理完成，但不自动关闭（由上层控制关闭时机）
        logger.info(f"错误处理完成 (会话: {session_id})")

    async def close(self) -> None:
        """关闭处理器"""
        if self._closed:
            return

        self._closed = True
        
        # 停止心跳任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # 刷新缓冲区
        await self._flush_buffer()
        
        # 发送关闭事件
        try:
            await self._send_status_update(
                "connection_closing",
                {
                    "active_tools_count": len(self.active_tools),
                    "message_active": self._is_message_active,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"发送关闭事件失败: {e}")
        
        # 清理状态
        self.active_tools.clear()
        self._message_buffer = ""
        self._is_message_active = False
        self._event_buffer.clear()

    async def _write_sse_event(self, event: StreamEvent) -> None:
        """写入SSE格式事件"""
        if self._closed:
            return
            
        try:
            sse_data = event.to_sse_format()
            await self.response_writer(sse_data)
            self._last_heartbeat = datetime.now()
        except Exception as e:
            logger.error(f"写入SSE事件失败: {e}")
            raise

    async def _send_status_update(self, status_type: str, data: Dict[str, Any]) -> None:
        """发送状态更新事件"""
        status_event = StreamEvent(
            event_type=StreamEventType.PROCESSING_STATUS,
            data={
                "status_type": status_type,
                "status_message": f"状态更新: {status_type}",
                **data
            }
        )
        await self._write_sse_event(status_event)

    async def _flush_buffer(self) -> None:
        """刷新事件缓冲区"""
        if not self._event_buffer:
            return
            
        for event in self._event_buffer:
            await self._write_sse_event(event)
        
        self._event_buffer.clear()

    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        if self._closed:
            return
            
        try:
            heartbeat_data = f"event: heartbeat\ndata: {{'timestamp': '{datetime.now().isoformat()}'}}\n\n"
            await self.response_writer(heartbeat_data)
            self._last_heartbeat = datetime.now()
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while not self._closed:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if not self._closed:
                    now = datetime.now()
                    if (now - self._last_heartbeat).total_seconds() >= self.heartbeat_interval:
                        await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")

    # 便捷方法
    def enable_metadata(self) -> None:
        """启用元数据显示"""
        self.include_metadata = True

    def disable_metadata(self) -> None:
        """禁用元数据显示"""
        self.include_metadata = False

    def enable_buffering(self) -> None:
        """启用事件缓冲"""
        self.buffer_events = True

    def disable_buffering(self) -> None:
        """禁用事件缓冲"""
        self.buffer_events = False

    def set_heartbeat_interval(self, interval: float) -> None:
        """设置心跳间隔"""
        self.heartbeat_interval = interval

    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态信息"""
        return {
            "is_closed": self._closed,
            "is_message_active": self._is_message_active,
            "active_tools_count": len(self.active_tools),
            "active_tools": list(self.active_tools.keys()),
            "buffer_size": len(self._event_buffer),
            "last_heartbeat": self._last_heartbeat.isoformat(),
            "heartbeat_interval": self.heartbeat_interval,
            "include_metadata": self.include_metadata,
            "buffer_events": self.buffer_events
        }

    async def send_custom_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """发送自定义SSE事件"""
        if self._closed:
            return

        try:
            custom_data = f"event: {event_type}\ndata: {data}\n\n"
            await self.response_writer(custom_data)
            self._last_heartbeat = datetime.now()
        except Exception as e:
            logger.error(f"发送自定义事件失败: {e}")

    async def force_flush(self) -> None:
        """强制刷新所有缓冲数据"""
        await self._flush_buffer()

    def is_healthy(self) -> bool:
        """检查处理器是否健康"""
        if self._closed:
            return False

        # 检查心跳是否正常
        if self.heartbeat_interval > 0:
            time_since_heartbeat = (datetime.now() - self._last_heartbeat).total_seconds()
            if time_since_heartbeat > self.heartbeat_interval * 2:
                return False

        return True
