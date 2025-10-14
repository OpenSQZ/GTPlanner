"""
SSE GTPlanner API

提供完整的流式响应 API 功能，支持实时工具调用状态更新和前端集成。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from ..context_types import AgentContext, AgentResult
from ..streaming.stream_types import (
    StreamEvent, StreamEventBuilder, StreamEventType,
    ToolCallStatus, AssistantMessageChunk
)
from ..gtplanner import GTPlanner

logger = logging.getLogger(__name__)


class SSEGTPlanner:
    """
    SSE GTPlanner API 类
    
    提供流式响应处理能力，支持实时工具调用状态更新。
    """

    def __init__(self, verbose: bool = False):
        """
        初始化 SSE GTPlanner
        
        Args:
            verbose: 是否启用详细日志
        """
        self.verbose = verbose
        self.gtplanner = GTPlanner(verbose=verbose)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        if verbose:
            logger.info("🚀 SSE GTPlanner API 初始化完成")

    async def process_request_stream(
        self,
        agent_context: Dict[str, Any],
        language: str = "zh",
        response_writer: Optional[Callable[[str], None]] = None,
        include_metadata: bool = False,
        buffer_events: bool = False,
        heartbeat_interval: float = 30.0
    ) -> Dict[str, Any]:
        """
        处理请求并生成流式响应
        
        Args:
            agent_context: Agent上下文数据
            language: 语言设置
            response_writer: 响应写入函数
            include_metadata: 是否包含元数据
            buffer_events: 是否缓冲事件
            heartbeat_interval: 心跳间隔（秒）
            
        Returns:
            处理结果
        """
        session_id = agent_context.get("session_id", "unknown")
        start_time = datetime.now()
        
        try:
            # 记录活跃会话
            self.active_sessions[session_id] = {
                "start_time": start_time,
                "status": "processing",
                "language": language
            }

            # 发送对话开始事件
            user_input = self._extract_user_input(agent_context)
            await self._send_event(
                StreamEventBuilder.conversation_start(session_id, user_input),
                response_writer
            )

            # 构建 AgentContext 对象
            context = AgentContext.from_dict(agent_context)
            
            # 创建流式回调
            streaming_callbacks = self._create_streaming_callbacks(
                session_id, response_writer, include_metadata
            )

            # 处理请求
            result = await self.gtplanner.process_request(
                context=context,
                language=language,
                streaming_callbacks=streaming_callbacks
            )

            # 发送对话结束事件
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._send_event(
                StreamEventBuilder.conversation_end(
                    session_id,
                    {
                        "success": result.success,
                        "execution_time": execution_time,
                        "new_messages_count": len(result.new_messages),
                        "metadata": result.metadata
                    },
                    result.tool_execution_results_updates
                ),
                response_writer
            )

            # 更新会话状态
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["end_time"] = datetime.now()

            return {
                "success": result.success,
                "session_id": session_id,
                "execution_time": execution_time,
                "new_messages": [msg.to_dict() for msg in result.new_messages],
                "tool_execution_results_updates": result.tool_execution_results_updates,
                "metadata": result.metadata,
                "error": result.error
            }

        except Exception as e:
            logger.error(f"处理请求时出错: {e}", exc_info=True)
            
            # 发送错误事件
            await self._send_event(
                StreamEventBuilder.error(
                    session_id,
                    str(e),
                    {"error_type": type(e).__name__}
                ),
                response_writer
            )

            # 更新会话状态
            self.active_sessions[session_id]["status"] = "failed"
            self.active_sessions[session_id]["error"] = str(e)
            self.active_sessions[session_id]["end_time"] = datetime.now()

            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

        finally:
            # 清理活跃会话（延迟清理，保留一段时间用于调试）
            asyncio.create_task(self._cleanup_session(session_id, delay=300))

    def _create_streaming_callbacks(
        self,
        session_id: str,
        response_writer: Optional[Callable[[str], None]],
        include_metadata: bool
    ) -> Dict[str, Callable]:
        """创建流式回调函数"""
        
        async def on_llm_start(data: Dict[str, Any]) -> None:
            """LLM 开始回调"""
            await self._send_event(
                StreamEventBuilder.assistant_message_start(session_id),
                response_writer
            )

        async def on_llm_chunk(data: Dict[str, Any]) -> None:
            """LLM 流式数据回调"""
            content = data.get("content", "")
            if content:
                chunk = AssistantMessageChunk(
                    content=content,
                    is_complete=False,
                    chunk_index=data.get("chunk_index", 0),
                    total_chunks=data.get("total_chunks")
                )
                await self._send_event(
                    StreamEventBuilder.assistant_message_chunk(session_id, chunk),
                    response_writer
                )

        async def on_llm_end(data: Dict[str, Any]) -> None:
            """LLM 结束回调"""
            complete_message = data.get("complete_message", "")
            message_metadata = data.get("metadata") if include_metadata else None
            
            await self._send_event(
                StreamEventBuilder.assistant_message_end(
                    session_id, complete_message, message_metadata
                ),
                response_writer
            )

        async def on_tool_start(data: Dict[str, Any]) -> None:
            """工具调用开始回调"""
            tool_status = ToolCallStatus(
                tool_name=data.get("tool_name", "unknown"),
                status="starting",
                call_id=data.get("call_id"),
                progress_message=data.get("progress_message"),
                arguments=data.get("arguments")
            )
            await self._send_event(
                StreamEventBuilder.tool_call_start(session_id, tool_status),
                response_writer
            )

        async def on_tool_progress(data: Dict[str, Any]) -> None:
            """工具调用进度回调"""
            tool_status = ToolCallStatus(
                tool_name=data.get("tool_name", "unknown"),
                status="running",
                call_id=data.get("call_id"),
                progress_message=data.get("progress_message"),
                arguments=data.get("arguments")
            )
            await self._send_event(
                StreamEventBuilder.tool_call_progress(session_id, tool_status),
                response_writer
            )

        async def on_tool_end(data: Dict[str, Any]) -> None:
            """工具调用结束回调"""
            tool_status = ToolCallStatus(
                tool_name=data.get("tool_name", "unknown"),
                status=data.get("status", "completed"),
                call_id=data.get("call_id"),
                progress_message=data.get("progress_message"),
                arguments=data.get("arguments"),
                result=data.get("result"),
                execution_time=data.get("execution_time"),
                error_message=data.get("error_message")
            )
            await self._send_event(
                StreamEventBuilder.tool_call_end(session_id, tool_status),
                response_writer
            )

        async def on_processing_status(data: Dict[str, Any]) -> None:
            """处理状态回调"""
            await self._send_event(
                StreamEventBuilder.processing_status(
                    session_id,
                    data.get("status_message", ""),
                    data.get("progress_info") if include_metadata else None
                ),
                response_writer
            )

        async def on_error(data: Dict[str, Any]) -> None:
            """错误回调"""
            await self._send_event(
                StreamEventBuilder.error(
                    session_id,
                    data.get("error_message", "未知错误"),
                    data.get("error_details") if include_metadata else None
                ),
                response_writer
            )

        return {
            "on_llm_start": on_llm_start,
            "on_llm_chunk": on_llm_chunk,
            "on_llm_end": on_llm_end,
            "on_tool_start": on_tool_start,
            "on_tool_progress": on_tool_progress,
            "on_tool_end": on_tool_end,
            "on_processing_status": on_processing_status,
            "on_error": on_error
        }

    async def _send_event(
        self,
        event: StreamEvent,
        response_writer: Optional[Callable[[str], None]]
    ) -> None:
        """发送流式事件"""
        if response_writer:
            try:
                sse_data = event.to_sse_format()
                if asyncio.iscoroutinefunction(response_writer):
                    await response_writer(sse_data)
                else:
                    response_writer(sse_data)
            except Exception as e:
                logger.error(f"发送事件失败: {e}")

    def _extract_user_input(self, agent_context: Dict[str, Any]) -> str:
        """从上下文提取用户输入"""
        dialogue_history = agent_context.get("dialogue_history", [])
        if dialogue_history:
            # 查找最后一条用户消息
            for message in reversed(dialogue_history):
                if message.get("role") == "user":
                    return message.get("content", "")
        return "未知输入"

    async def _cleanup_session(self, session_id: str, delay: int = 300) -> None:
        """延迟清理会话"""
        await asyncio.sleep(delay)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            if self.verbose:
                logger.info(f"清理会话: {session_id}")

    def get_api_status(self) -> Dict[str, Any]:
        """获取 API 状态信息"""
        active_count = len(self.active_sessions)
        
        return {
            "status": "running",
            "active_sessions": active_count,
            "sessions": list(self.active_sessions.keys()),
            "gtplanner_status": "ready" if self.gtplanner else "not_initialized",
            "verbose_mode": self.verbose,
            "timestamp": datetime.now().isoformat()
        }

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话状态"""
        return self.active_sessions.get(session_id)

    async def close(self) -> None:
        """关闭 API"""
        if self.verbose:
            logger.info("🔄 关闭 SSE GTPlanner API")
        
        # 清理所有活跃会话
        self.active_sessions.clear()
        
        if self.verbose:
            logger.info("✅ SSE GTPlanner API 已关闭")