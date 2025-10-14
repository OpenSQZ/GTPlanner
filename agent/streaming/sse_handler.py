"""
SSE 事件处理器

专门为 Server-Sent Events (SSE) 设计的流式事件处理器，
支持 HTTP SSE 客户端的实时数据流处理。
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from .stream_types import StreamEvent, StreamEventType
from .stream_interface import StreamHandler

logger = logging.getLogger(__name__)


class SSEHandler(StreamHandler):
    """
    SSE 流式事件处理器
    
    专门为 HTTP SSE 客户端设计，负责将流式事件转换为 SSE 格式数据流。
    支持实时工具调用状态更新和前端集成。
    """

    def __init__(
        self,
        response_writer: Optional[Callable[[str], None]] = None,
        include_metadata: bool = False,
        buffer_size: int = 100,
        auto_heartbeat: bool = True,
        heartbeat_interval: float = 30.0
    ):
        """
        初始化 SSE 处理器
        
        Args:
            response_writer: 响应写入函数
            include_metadata: 是否包含元数据
            buffer_size: 事件缓冲区大小
            auto_heartbeat: 是否自动发送心跳
            heartbeat_interval: 心跳间隔（秒）
        """
        self.response_writer = response_writer
        self.include_metadata = include_metadata
        self.buffer_size = buffer_size
        self.auto_heartbeat = auto_heartbeat
        self.heartbeat_interval = heartbeat_interval
        
        # 状态管理
        self._closed = False
        self._event_buffer: List[StreamEvent] = []
        self._last_heartbeat = datetime.now()
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # 会话统计
        self.event_count = 0
        self.start_time = datetime.now()
        
        # 启动心跳任务
        if self.auto_heartbeat:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def handle_event(self, event: StreamEvent) -> None:
        """处理单个流式事件"""
        if self._closed:
            return

        try:
            self.event_count += 1
            
            # 更新事件时间戳
            if not event.timestamp:
                event.timestamp = datetime.now().isoformat()
            
            # 添加到缓冲区（如果需要）
            if self.buffer_size > 0:
                self._event_buffer.append(event)
                if len(self._event_buffer) > self.buffer_size:
                    self._event_buffer.pop(0)
            
            # 转换为 SSE 格式并发送
            sse_data = self._format_sse_event(event)
            await self._write_response(sse_data)
            
            # 记录日志
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"SSE事件已发送: {event.event_type.value}")

        except Exception as e:
            logger.error(f"处理SSE事件失败: {e}", exc_info=True)
            await self.handle_error(e, event.session_id)

    async def _format_sse_event(self, event: StreamEvent) -> str:
        """将事件格式化为 SSE 格式"""
        # 构建基础事件数据
        event_data = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "data": event.data
        }
        
        # 添加元数据（如果需要）
        if self.include_metadata:
            event_data["metadata"] = {
                "event_index": self.event_count,
                "processing_time": (datetime.now() - self.start_time).total_seconds(),
                "buffer_size": len(self._event_buffer),
                "original_metadata": event.metadata
            }
        
        # 转换为 JSON 并格式化 SSE
        json_data = json.dumps(event_data, ensure_ascii=False)
        return f"event: {event.event_type.value}\ndata: {json_data}\n\n"

    async def _write_response(self, data: str) -> None:
        """写入响应数据"""
        if self.response_writer:
            try:
                if asyncio.iscoroutinefunction(self.response_writer):
                    await self.response_writer(data)
                else:
                    self.response_writer(data)
            except Exception as e:
                logger.error(f"写入响应数据失败: {e}")
                raise

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while not self._closed:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self._closed:
                    await self._send_heartbeat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")

    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        try:
            heartbeat_data = {
                "timestamp": datetime.now().isoformat(),
                "session_duration": (datetime.now() - self.start_time).total_seconds(),
                "event_count": self.event_count,
                "buffer_size": len(self._event_buffer)
            }
            
            json_data = json.dumps(heartbeat_data, ensure_ascii=False)
            heartbeat_sse = f"event: heartbeat\ndata: {json_data}\n\n"
            
            await self._write_response(heartbeat_sse)
            self._last_heartbeat = datetime.now()
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("SSE心跳已发送")
                
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")

    async def handle_error(self, error: Exception, session_id: Optional[str] = None) -> None:
        """处理错误"""
        if self._closed:
            return

        try:
            error_data = {
                "error_message": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "event_count": self.event_count
            }
            
            if self.include_metadata:
                error_data["metadata"] = {
                    "session_duration": (datetime.now() - self.start_time).total_seconds(),
                    "buffer_size": len(self._event_buffer)
                }
            
            json_data = json.dumps(error_data, ensure_ascii=False)
            error_sse = f"event: error\ndata: {json_data}\n\n"
            
            await self._write_response(error_sse)
            
        except Exception as e:
            logger.error(f"处理错误事件失败: {e}")

    async def send_connection_event(self, session_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        """发送连接建立事件"""
        connection_data = {
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "config": config or {},
            "server_info": {
                "version": "1.0.0",
                "sse_handler": "SSEHandler",
                "features": ["streaming", "heartbeat", "metadata"]
            }
        }
        
        json_data = json.dumps(connection_data, ensure_ascii=False)
        connection_sse = f"event: connection\ndata: {json_data}\n\n"
        
        await self._write_response(connection_sse)

    async def send_completion_event(self, result: Dict[str, Any]) -> None:
        """发送完成事件"""
        completion_data = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "statistics": {
                "total_events": self.event_count,
                "session_duration": (datetime.now() - self.start_time).total_seconds(),
                "buffer_size": len(self._event_buffer)
            }
        }
        
        json_data = json.dumps(completion_data, ensure_ascii=False)
        completion_sse = f"event: complete\ndata: {json_data}\n\n"
        
        await self._write_response(completion_sse)

    async def send_close_event(self, message: str = "Stream completed successfully") -> None:
        """发送连接关闭事件"""
        close_data = {
            "status": "closing",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "final_statistics": {
                "total_events": self.event_count,
                "session_duration": (datetime.now() - self.start_time).total_seconds()
            }
        }
        
        json_data = json.dumps(close_data, ensure_ascii=False)
        close_sse = f"event: close\ndata: {json_data}\n\n"
        
        await self._write_response(close_sse)

    async def close(self) -> None:
        """关闭处理器"""
        if self._closed:
            return

        self._closed = True
        
        # 取消心跳任务
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 发送关闭事件
        try:
            await self.send_close_event()
        except Exception as e:
            logger.error(f"发送关闭事件失败: {e}")
        
        logger.info(f"SSE处理器已关闭，共处理 {self.event_count} 个事件")

    def get_statistics(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "event_count": self.event_count,
            "session_duration": (datetime.now() - self.start_time).total_seconds(),
            "buffer_size": len(self._event_buffer),
            "last_heartbeat": self._last_heartbeat.isoformat(),
            "is_closed": self._closed,
            "include_metadata": self.include_metadata,
            "auto_heartbeat": self.auto_heartbeat,
            "heartbeat_interval": self.heartbeat_interval
        }

    def get_buffered_events(self) -> List[Dict[str, Any]]:
        """获取缓冲区中的事件"""
        return [event.to_dict() for event in self._event_buffer]

    def clear_buffer(self) -> None:
        """清空事件缓冲区"""
        self._event_buffer.clear()

    # 便捷方法
    def enable_metadata(self) -> None:
        """启用元数据"""
        self.include_metadata = True

    def disable_metadata(self) -> None:
        """禁用元数据"""
        self.include_metadata = False

    def set_heartbeat_interval(self, interval: float) -> None:
        """设置心跳间隔"""
        self.heartbeat_interval = interval

    def enable_heartbeat(self) -> None:
        """启用心跳"""
        if not self.auto_heartbeat and not self._closed:
            self.auto_heartbeat = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def disable_heartbeat(self) -> None:
        """禁用心跳"""
        self.auto_heartbeat = False
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()