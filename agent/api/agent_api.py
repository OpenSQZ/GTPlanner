#!/usr/bin/env python3
"""
GTPlanner SSE API

基于新的流式响应架构的API实现：
1. 集成StreamingSession和SSEStreamHandler
2. 使用StatelessGTPlanner而不是旧的ReActOrchestratorFlow
3. 支持类型安全的流式响应（StreamEventType/StreamCallbackType）
4. 移除会话管理功能，专注于单次请求处理
5. 优雅的错误处理和资源清理

使用方式:
    ```python
    from agent.api.agent_api import SSEGTPlanner
    
    api = SSEGTPlanner(verbose=True)
    
    async def write_sse_data(data: str):
        await response.write(data)
    
    await api.process_request_stream(
        user_input="设计用户管理系统",
        response_writer=write_sse_data,
        include_metadata=True,
        buffer_events=False
    )
    ```
"""

import sys
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入新的流式响应架构
from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, Message, MessageRole
from agent.streaming import StreamingSession, streaming_manager

# 导入SSE处理器
from agent.streaming.sse_handler import SSEStreamHandler


logger = logging.getLogger(__name__)


class SSEGTPlanner:
    """基于新流式响应架构的GTPlanner SSE API"""

    def __init__(self, 
                 include_metadata: bool = False,
                 buffer_events: bool = False,
                 heartbeat_interval: float = 30.0,
                 verbose: bool = False):
        """
        初始化SSE API
        
        Args:
            include_metadata: 是否包含详细元数据
            buffer_events: 是否缓冲事件以优化传输
            heartbeat_interval: 心跳间隔（秒）
            verbose: 是否显示详细日志信息
        """
        self.include_metadata = include_metadata
        self.buffer_events = buffer_events
        self.heartbeat_interval = heartbeat_interval
        self.verbose = verbose
        
        # 配置日志级别
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        # 使用新的StatelessGTPlanner
        self.planner = StatelessGTPlanner()
        
        # 流式响应组件
        self.current_streaming_session: Optional[StreamingSession] = None
        self.sse_handler: Optional[SSEStreamHandler] = None
        
        logger.info("SSE GTPlanner API 初始化完成")
    
    async def _cleanup_streaming_session(self):
        """清理流式会话资源"""
        if self.current_streaming_session:
            try:
                await self.current_streaming_session.stop()
                self.current_streaming_session = None
                self.sse_handler = None
                logger.debug("流式会话资源清理完成")
            except Exception as e:
                logger.error(f"清理流式会话时出错: {e}")
    
    def _create_sse_streaming_session(
        self, 
        session_id: str, 
        response_writer: Callable[[str], Awaitable[None]]
    ) -> StreamingSession:
        """创建SSE流式会话和处理器"""
        # 创建流式会话
        streaming_session = streaming_manager.create_session(session_id)
        
        # 创建SSE处理器
        sse_handler = SSEStreamHandler(
            response_writer=response_writer,
            include_metadata=self.include_metadata,
            buffer_events=self.buffer_events,
            heartbeat_interval=self.heartbeat_interval
        )
        
        # 添加处理器到会话
        streaming_session.add_handler(sse_handler)
        
        # 保存引用以便清理
        self.sse_handler = sse_handler
        
        logger.debug(f"创建SSE流式会话: {session_id}")
        return streaming_session
    
    def _validate_and_parse_agent_context(self, context_data: Dict[str, Any]) -> AgentContext:
        """
        验证并解析前端传递的 AgentContext 数据

        Args:
            context_data: 前端传递的 AgentContext 数据

        Returns:
            AgentContext实例

        Raises:
            ValueError: 当 AgentContext 数据格式不正确时
        """
        try:
            # 直接使用 AgentContext.from_dict 进行验证和解析
            context = AgentContext.from_dict(context_data)

            # 验证必需字段
            if not context.session_id or not isinstance(context.session_id, str):
                raise ValueError("session_id 必须是非空字符串")

            if not context.dialogue_history:
                raise ValueError("dialogue_history 不能为空")

            # 验证对话历史中至少有一条用户消息
            user_messages = [msg for msg in context.dialogue_history if msg.role == MessageRole.USER]
            if not user_messages:
                raise ValueError("对话历史中必须包含至少一条用户消息")

            logger.debug(f"验证AgentContext完成，会话ID: {context.session_id}, 消息数: {len(context.dialogue_history)}")
            return context

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"AgentContext 数据格式错误: {e}")
    
    async def process_request_stream(
        self,
        agent_context: Dict[str, Any],
        response_writer: Callable[[str], Awaitable[None]],
        language: Optional[str] = None,
        **config_options
    ) -> Dict[str, Any]:
        """
        处理用户请求并通过SSE流式返回结果

        Args:
            agent_context: 前端传递的完整 AgentContext 数据，包含：
                - session_id: 会话ID（必需）
                - dialogue_history: 对话历史（必需，包含用户输入）
                - tool_execution_results: 工具执行结果（可选）
                - session_metadata: 会话元数据（可选）
                - last_updated: 最后更新时间（可选）
                - is_compressed: 是否压缩（可选）
            response_writer: SSE数据写入函数
            language: 语言选择，支持 'zh', 'en', 'ja', 'es', 'fr'（可选）
            **config_options: 额外的配置选项

        Returns:
            处理结果摘要
        """
        # 应用配置选项
        original_config = self._apply_config_options(config_options)

        try:
            # 验证并解析AgentContext
            context = self._validate_and_parse_agent_context(agent_context)
            session_id = context.session_id

            # 获取最新的用户输入（对话历史中的最后一条用户消息）
            user_messages = [msg for msg in context.dialogue_history if msg.role == MessageRole.USER]
            latest_user_input = user_messages[-1].content if user_messages else ""

            logger.info(f"开始处理请求，会话ID: {session_id}, 用户输入长度: {len(latest_user_input)}")
            logger.debug(f"对话历史: {len(context.dialogue_history)} 条消息")

            # 创建SSE流式会话
            streaming_session = self._create_sse_streaming_session(session_id, response_writer)
            self.current_streaming_session = streaming_session

            # 启动流式会话
            await streaming_session.start()

            # 使用StatelessGTPlanner处理
            logger.debug("调用StatelessGTPlanner处理请求")
            result = await self.planner.process(latest_user_input, context, streaming_session, language=language)

            # 构建结果摘要
            result_summary = {
                "success": result.success,
                "session_id": session_id,
                "user_input": latest_user_input,
                "new_messages_count": len(result.new_messages) if result.new_messages else 0,
                "tool_execution_results_updates": result.tool_execution_results_updates if hasattr(result, 'tool_execution_results_updates') else {},
                "error": result.error if not result.success else None,
                "metadata": {
                    "include_metadata": self.include_metadata,
                    "buffer_events": self.buffer_events,
                    "heartbeat_interval": self.heartbeat_interval,
                    "context_compressed": context.is_compressed,
                    "dialogue_history_length": len(context.dialogue_history),
                    "tool_updates_count": len(result.tool_execution_results_updates) if hasattr(result, 'tool_execution_results_updates') else 0
                } if self.include_metadata else {}
            }

            if result.success:
                logger.info(f"请求处理成功，生成 {result_summary['new_messages_count']} 条新消息")
            else:
                logger.error(f"请求处理失败: {result.error}")

            return result_summary

        except ValueError as e:
            # AgentContext 数据验证错误
            logger.error(f"AgentContext 验证失败: {e}")
            error_session_id = agent_context.get('session_id', 'unknown')

            # 通过SSE发送错误信息
            if self.sse_handler:
                await self.sse_handler.handle_error(e, error_session_id)

            return {
                "success": False,
                "session_id": error_session_id,
                "user_input": "",  # 无法获取用户输入，因为验证失败
                "error": str(e),
                "error_type": "ValidationError"
            }

        except Exception as e:
            logger.error(f"处理请求时发生异常: {e}", exc_info=self.verbose)
            error_session_id = agent_context.get('session_id', 'unknown')

            # 通过SSE发送错误信息
            if self.sse_handler:
                await self.sse_handler.handle_error(e, error_session_id)

            return {
                "success": False,
                "session_id": error_session_id,
                "user_input": "",  # 无法获取用户输入，因为处理失败
                "error": str(e),
                "error_type": type(e).__name__
            }

        finally:
            # 恢复原始配置
            self._restore_config_options(original_config)
            
            # 清理流式会话
            await self._cleanup_streaming_session()
            
            logger.debug("请求处理完成，资源已清理")
    
    def _apply_config_options(self, config_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用配置选项并返回原始配置
        
        Args:
            config_options: 新的配置选项
            
        Returns:
            原始配置选项
        """
        original_config = {
            "include_metadata": self.include_metadata,
            "buffer_events": self.buffer_events,
            "heartbeat_interval": self.heartbeat_interval
        }
        
        # 应用新配置
        if "include_metadata" in config_options:
            self.include_metadata = config_options["include_metadata"]
        if "buffer_events" in config_options:
            self.buffer_events = config_options["buffer_events"]
        if "heartbeat_interval" in config_options:
            self.heartbeat_interval = config_options["heartbeat_interval"]
        
        return original_config
    
    def _restore_config_options(self, original_config: Dict[str, Any]):
        """恢复原始配置选项"""
        self.include_metadata = original_config["include_metadata"]
        self.buffer_events = original_config["buffer_events"]
        self.heartbeat_interval = original_config["heartbeat_interval"]
    
    async def process_simple_request(
        self,
        user_input: str,
        response_writer: Callable[[str], Awaitable[None]],
        session_id: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        简化的请求处理方法（向后兼容）

        Args:
            user_input: 用户输入
            response_writer: SSE数据写入函数
            session_id: 可选的会话ID，如果不提供将生成新的
            language: 语言选择，支持 'zh', 'en', 'ja', 'es', 'fr'（可选）

        Returns:
            处理结果
        """
        # 生成会话ID（如果未提供）
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

        # 构建简化的 AgentContext
        from datetime import datetime

        # 创建用户消息
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }

        agent_context = {
            "session_id": session_id,
            "dialogue_history": [user_message],
            "tool_execution_results": {},
            "session_metadata": {
                "created_at": datetime.now().isoformat(),
                "api_version": "1.0.0",
                "request_type": "simple"
            },
            "last_updated": datetime.now().isoformat(),
            "is_compressed": False
        }

        return await self.process_request_stream(
            agent_context=agent_context,
            response_writer=response_writer,
            language=language
        )
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API状态信息"""
        return {
            "api_name": "SSE GTPlanner API",
            "version": "1.0.0",
            "planner_type": "StatelessGTPlanner",
            "streaming_enabled": True,
            "current_config": {
                "include_metadata": self.include_metadata,
                "buffer_events": self.buffer_events,
                "heartbeat_interval": self.heartbeat_interval,
                "verbose": self.verbose
            },
            "active_session": self.current_streaming_session is not None,
            "session_id": getattr(self.current_streaming_session, 'session_id', None)
        }
    
    # 便捷配置方法
    def enable_metadata(self) -> None:
        """启用元数据"""
        self.include_metadata = True
        logger.debug("元数据显示已启用")

    def disable_metadata(self) -> None:
        """禁用元数据"""
        self.include_metadata = False
        logger.debug("元数据显示已禁用")

    def enable_buffering(self) -> None:
        """启用事件缓冲"""
        self.buffer_events = True
        logger.debug("事件缓冲已启用")

    def disable_buffering(self) -> None:
        """禁用事件缓冲"""
        self.buffer_events = False
        logger.debug("事件缓冲已禁用")

    def set_heartbeat_interval(self, interval: float) -> None:
        """设置心跳间隔"""
        self.heartbeat_interval = interval
        logger.debug(f"心跳间隔设置为: {interval}秒")


# 便捷函数
async def create_sse_response(
    user_input: str,
    response_writer: Callable[[str], Awaitable[None]],
    session_id: Optional[str] = None,
    **config_options
) -> Dict[str, Any]:
    """
    便捷函数：创建SSE响应（向后兼容）

    Args:
        user_input: 用户输入
        response_writer: SSE数据写入函数
        session_id: 可选的会话ID
        **config_options: 配置选项

    Returns:
        处理结果
    """
    api = SSEGTPlanner(**config_options)
    return await api.process_simple_request(user_input, response_writer, session_id)


async def create_sse_response_with_context(
    agent_context: Dict[str, Any],
    response_writer: Callable[[str], Awaitable[None]],
    **config_options
) -> Dict[str, Any]:
    """
    便捷函数：使用完整 AgentContext 创建SSE响应

    Args:
        agent_context: 完整的 AgentContext 数据
        response_writer: SSE数据写入函数
        **config_options: 配置选项

    Returns:
        处理结果
    """
    api = SSEGTPlanner(**config_options)
    return await api.process_request_stream(agent_context, response_writer)
