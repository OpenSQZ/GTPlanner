"""
无状态GTPlanner主入口

实现完全无状态的GTPlanner，原生支持流式响应。
不依赖任何全局状态或统一上下文系统，采用纯函数式设计。

设计原则：
1. 完全无状态：不维护任何实例变量或全局状态
2. 纯函数式：相同输入产生相同输出
3. 独立执行：每次调用都是完全独立的
4. 错误隔离：异常不影响其他请求的处理
5. 原生流式：内置流式响应支持，现代化用户体验
"""

import asyncio
from typing import Optional

from .context_types import AgentContext, AgentResult
from .pocketflow_factory import PocketFlowSharedFactory
from .flows.react_orchestrator_refactored.react_orchestrator_flow import ReActOrchestratorFlow
from .streaming.stream_types import StreamEventBuilder, AssistantMessageChunk, ToolCallStatus, StreamCallbackType
from .streaming.stream_interface import StreamingSession


class StatelessGTPlanner:
    """
    无状态GTPlanner - 纯函数式处理
    
    这是GTPlanner的新一代无状态实现，完全独立于统一上下文系统。
    每次调用都是独立的，不维护任何状态，支持高并发和水平扩展。
    """
    
    def __init__(self):
        """
        初始化无状态GTPlanner
        
        注意：这里不维护任何状态，只是为了保持接口一致性
        """
        # 不维护任何实例状态
        pass
    
    async def process(
        self,
        user_input: str,
        context: AgentContext,
        streaming_session: StreamingSession,
        language: Optional[str] = None
    ) -> AgentResult:
        """
        处理用户请求（纯函数，统一流式架构）

        Args:
            user_input: 用户输入
            context: Agent上下文（只读，可能已压缩）
            streaming_session: 流式会话（必填）
            language: 语言选择，支持 'zh', 'en', 'ja', 'es', 'fr'（可选）

        Returns:
            处理结果对象
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 流式响应：发送对话开始事件
            await streaming_session.emit_event(
                StreamEventBuilder.conversation_start(streaming_session.session_id, user_input)
            )
            await streaming_session.emit_event(
                StreamEventBuilder.processing_status(
                    streaming_session.session_id,
                    "正在初始化处理环境..."
                )
            )

            # 1. 使用工厂创建独立的pocketflow shared字典
            shared = PocketFlowSharedFactory.create_shared_dict(user_input, context, language=language)

            # 2. 注入流式回调（统一流式架构）
            shared["streaming_session"] = streaming_session
            shared["streaming_callbacks"] = {
                StreamCallbackType.ON_LLM_START: self._on_llm_start,
                StreamCallbackType.ON_LLM_CHUNK: self._on_llm_chunk,
                StreamCallbackType.ON_LLM_END: self._on_llm_end,
                StreamCallbackType.ON_TOOL_START: self._on_tool_start,
                StreamCallbackType.ON_TOOL_PROGRESS: self._on_tool_progress,
                StreamCallbackType.ON_TOOL_END: self._on_tool_end
            }

            # 3. 创建独立的orchestrator实例
            orchestrator = ReActOrchestratorFlow()

            # 4. 执行处理（完全独立的执行环境）
            await orchestrator.run_async(shared)

            # 5. 计算执行时间
            execution_time = asyncio.get_event_loop().time() - start_time

            # 6. 从shared字典创建结果
            result = PocketFlowSharedFactory.create_agent_result(
                shared, execution_time=execution_time
            )

            # 流式响应：发送对话结束事件
            await streaming_session.emit_event(
                StreamEventBuilder.conversation_end(
                    streaming_session.session_id,
                    {
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "new_messages_count": len(result.new_messages)
                    },
                    tool_execution_results_updates=result.tool_execution_results_updates
                )
            )

            return result
            
        except Exception as e:
            # 错误处理：创建错误结果，不影响其他请求
            execution_time = asyncio.get_event_loop().time() - start_time

            # 流式响应：发送错误事件
            await streaming_session.emit_event(
                StreamEventBuilder.error(
                    streaming_session.session_id,
                    f"Processing failed: {str(e)}",
                    {"exception_type": type(e).__name__}
                )
            )
            
            return AgentResult.create_error(
                error=f"Processing failed: {str(e)}",
                metadata={
                    "error_type": type(e).__name__,
                    "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
                    "context_session_id": context.session_id,

                    "is_compressed": context.is_compressed
                },
                execution_time=execution_time
            )

    # 流式回调方法（静态方法，保持无状态特性）
    @staticmethod
    async def _on_llm_start(session: StreamingSession, **kwargs) -> None:
        """LLM开始响应回调"""
        await session.emit_event(
            StreamEventBuilder.assistant_message_start(session.session_id)
        )

    @staticmethod
    async def _on_llm_chunk(
        session: StreamingSession,
        chunk_content: str,
        chunk_index: int = 0,
        **kwargs
    ) -> None:
        """LLM响应片段回调"""
        chunk = AssistantMessageChunk(
            content=chunk_content,
            is_complete=False,
            chunk_index=chunk_index
        )

        await session.emit_event(
            StreamEventBuilder.assistant_message_chunk(session.session_id, chunk)
        )

    @staticmethod
    async def _on_llm_end(
        session: StreamingSession,
        complete_message: str,
        message_metadata: Optional[dict] = None,
        tool_calls: Optional[list] = None,
        **kwargs
    ) -> None:
        """LLM响应结束回调"""
        # 如果有 tool_calls，将其添加到 message_metadata 中
        if message_metadata is None:
            message_metadata = {}

        if tool_calls:
            message_metadata["tool_calls"] = tool_calls

        await session.emit_event(
            StreamEventBuilder.assistant_message_end(
                session.session_id,
                complete_message,
                message_metadata
            )
        )

    @staticmethod
    async def _on_tool_start(
        session: StreamingSession,
        tool_name: str,
        arguments: dict,
        call_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """工具调用开始回调（事件由ToolExecutor发送，此处仅作为占位符）"""
        # 注意：实际的tool_call_start事件由ToolExecutor发送，避免重复
        # call_id 参数已添加以匹配新的回调签名
        pass

    @staticmethod
    async def _on_tool_progress(
        session: StreamingSession,
        tool_name: str,
        progress_message: str,
        **kwargs
    ) -> None:
        """工具调用进度回调"""
        tool_status = ToolCallStatus(
            tool_name=tool_name,
            status="running",
            progress_message=progress_message
        )

        await session.emit_event(
            StreamEventBuilder.tool_call_progress(session.session_id, tool_status)
        )

    @staticmethod
    async def _on_tool_end(
        session: StreamingSession,
        tool_name: str,
        result: dict,
        execution_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs
    ) -> None:
        """工具调用结束回调（事件由ToolExecutor发送，此处仅作为占位符）"""
        # 注意：实际的tool_call_end事件由ToolExecutor发送，避免重复
        pass


# 便捷函数

async def process_user_request(
    user_input: str,
    context: AgentContext,
    streaming_session: Optional[StreamingSession] = None
) -> AgentResult:
    """
    处理用户请求的便捷函数（支持流式响应）

    Args:
        user_input: 用户输入
        context: Agent上下文
        streaming_session: 可选的流式会话

    Returns:
        处理结果
    """
    planner = StatelessGTPlanner()
    return await planner.process(user_input, context, streaming_session)





# 向后兼容的别名
StatelessGTPlanner = StatelessGTPlanner
