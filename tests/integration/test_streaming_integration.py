"""
流式响应系统集成测试

测试流式响应系统与其他组件的集成
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.streaming import (
    StreamEvent,
    StreamEventType,
    StreamEventBuilder,
    StreamingSession,
    StreamingManager,
    streaming_manager
)
from agent.base_node import BaseAgentNode
from utils.error_handler import get_error_handler, reset_error_handler


class TestStreamingIntegration:
    """流式响应系统集成测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()

    @pytest.mark.asyncio
    async def test_streaming_session_creation(self):
        """测试流式会话创建"""
        session = StreamingSession("test-session-001")
        
        assert session.session_id == "test-session-001"
        assert session.is_active is False
        assert len(session.handlers) == 0
        assert isinstance(session.metadata, dict)

    @pytest.mark.asyncio
    async def test_streaming_event_builder(self):
        """测试流式事件构建器"""
        session_id = "test-session-002"
        
        # 测试对话开始事件
        start_event = StreamEventBuilder.conversation_start(
            session_id,
            "测试输入"  # 根据实际实现，这里应该是字符串而不是字典
        )

        assert start_event.event_type == StreamEventType.CONVERSATION_START
        assert start_event.session_id == session_id
        assert start_event.data["user_input"] == "测试输入"
        
        # 测试消息块事件
        from agent.streaming.stream_types import AssistantMessageChunk
        chunk = AssistantMessageChunk(
            content="测试消息"
        )

        chunk_event = StreamEventBuilder.assistant_message_chunk(session_id, chunk)
        assert chunk_event.event_type == StreamEventType.ASSISTANT_MESSAGE_CHUNK
        assert chunk_event.data["content"] == "测试消息"
        
        # 测试错误事件
        error_event = StreamEventBuilder.error(
            session_id,
            "测试错误",
            {"error_code": "TEST_ERROR"}
        )
        
        assert error_event.event_type == StreamEventType.ERROR
        assert error_event.data["error_message"] == "测试错误"

    @pytest.mark.asyncio
    async def test_streaming_session_with_handlers(self):
        """测试带处理器的流式会话"""
        session = StreamingSession("test-session-003")
        
        # 创建模拟处理器
        mock_handler = AsyncMock()
        mock_handler.handle_event = AsyncMock()
        mock_handler.handle_error = AsyncMock()
        
        # 添加处理器
        session.add_handler(mock_handler)
        assert len(session.handlers) == 1
        
        # 发送事件
        test_event = StreamEvent(
            event_type=StreamEventType.PROCESSING_STATUS,
            session_id="test-session-003",
            data={"status": "processing"}
        )
        
        await session.emit_event(test_event)
        
        # 验证处理器被调用
        mock_handler.handle_event.assert_called_once_with(test_event)
        
        # 移除处理器
        session.remove_handler(mock_handler)
        assert len(session.handlers) == 0

    @pytest.mark.asyncio
    async def test_streaming_session_error_handling(self):
        """测试流式会话错误处理"""
        session = StreamingSession("test-session-004")
        
        # 创建会抛出异常的处理器
        error_handler = AsyncMock()
        error_handler.handle_event = AsyncMock(side_effect=Exception("Handler error"))
        error_handler.handle_error = AsyncMock()
        
        # 创建正常的处理器
        normal_handler = AsyncMock()
        normal_handler.handle_event = AsyncMock()
        normal_handler.handle_error = AsyncMock()
        
        # 添加两个处理器
        session.add_handler(error_handler)
        session.add_handler(normal_handler)
        
        # 发送事件
        test_event = StreamEvent(
            event_type=StreamEventType.PROCESSING_STATUS,
            session_id="test-session-004",
            data={"status": "processing"}
        )
        
        await session.emit_event(test_event)
        
        # 验证错误处理器的错误被处理
        error_handler.handle_error.assert_called_once()
        
        # 验证正常处理器仍然被调用
        normal_handler.handle_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_streaming_manager_integration(self):
        """测试流式管理器集成"""
        manager = streaming_manager
        
        # 创建会话
        session_id = "test-session-005"
        session = manager.create_session(session_id)
        
        assert session.session_id == session_id
        assert session_id in manager.sessions

        # 获取会话
        retrieved_session = manager.get_session(session_id)
        assert retrieved_session is session

        # 关闭会话
        await manager.close_session(session_id)
        assert session_id not in manager.sessions

    @pytest.mark.asyncio
    async def test_base_node_streaming_integration(self):
        """测试基础节点与流式系统集成"""
        class TestStreamingNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True, "result": "streaming_test"}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                shared["streaming_result"] = exec_res["result"]
                return "success"
        
        # 创建节点和流式会话
        node = TestStreamingNode("streaming_test_node")
        session = StreamingSession("test-session-006")
        
        # 创建模拟处理器来捕获事件
        captured_events = []
        
        class EventCapture:
            async def handle_event(self, event):
                captured_events.append(event)
            
            async def handle_error(self, error, session_id):
                captured_events.append(("error", error, session_id))
        
        session.add_handler(EventCapture())
        
        # 执行节点流程
        shared = {"streaming_session": session}
        
        with patch('agent.base_node.emit_processing_status') as mock_emit:
            prep_res = await node.prep_async(shared)
            exec_res = await node.exec_async(prep_res)
            next_action = await node.post_async(shared, prep_res, exec_res)
        
        # 验证流程执行成功
        assert next_action == "success"
        assert shared["streaming_result"] == "streaming_test"
        
        # 验证流式事件被发送
        assert mock_emit.call_count >= 2  # 开始和完成事件

    @pytest.mark.asyncio
    async def test_error_handler_streaming_integration(self):
        """测试错误处理器与流式系统集成"""
        error_handler = get_error_handler()
        session = StreamingSession("test-session-007")
        
        # 创建事件捕获器
        captured_events = []
        
        class EventCapture:
            async def handle_event(self, event):
                captured_events.append(event)
            
            async def handle_error(self, error, session_id):
                captured_events.append(("error", error, session_id))
        
        session.add_handler(EventCapture())
        
        # 记录错误（模拟在流式上下文中）
        shared = {"streaming_session": session}
        
        error_context = error_handler.record_error(
            shared=shared,
            source="streaming_integration_test",
            error="Streaming integration error",
            session_id="test-session-007"
        )
        
        # 验证错误被正确记录
        assert error_context.session_id == "test-session-007"
        assert "errors" in shared
        
        # 验证错误历史
        summary = error_handler.get_error_summary(session_id="test-session-007")
        assert summary["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_streaming_sessions(self):
        """测试并发流式会话"""
        manager = streaming_manager
        
        # 创建多个并发会话
        session_ids = [f"concurrent-session-{i}" for i in range(5)]
        sessions = []
        
        for session_id in session_ids:
            session = manager.create_session(session_id)
            sessions.append(session)
        
        # 验证所有会话都被创建
        assert len(manager.sessions) >= 5
        
        # 并发发送事件
        async def send_events(session):
            for i in range(3):
                event = StreamEvent(
                    event_type=StreamEventType.PROCESSING_STATUS,
                    session_id=session.session_id,
                    data={"step": i}
                )
                await session.emit_event(event)
        
        # 并发执行
        await asyncio.gather(*[send_events(session) for session in sessions])
        
        # 清理会话
        for session_id in session_ids:
            await manager.close_session(session_id)

    @pytest.mark.asyncio
    async def test_streaming_event_serialization(self):
        """测试流式事件序列化"""
        # 创建复杂的事件数据
        complex_data = {
            "user_input": "复杂的用户输入",
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "language": "zh",
                "nested": {
                    "level": 2,
                    "items": [1, 2, 3]
                }
            },
            "unicode_text": "这是中文测试 🚀"
        }
        
        event = StreamEvent(
            event_type=StreamEventType.CONVERSATION_START,
            session_id="serialization-test",
            data=complex_data
        )
        
        # 测试事件可以被序列化
        import json
        serialized = json.dumps(event.to_dict(), ensure_ascii=False)
        
        # 测试反序列化
        deserialized_dict = json.loads(serialized)
        
        # 验证数据完整性
        assert deserialized_dict["event_type"] == "conversation_start"
        assert deserialized_dict["session_id"] == "serialization-test"
        assert deserialized_dict["data"]["unicode_text"] == "这是中文测试 🚀"

    @pytest.mark.asyncio
    async def test_streaming_performance(self):
        """测试流式响应性能"""
        session = StreamingSession("performance-test")
        
        # 创建高性能处理器
        class PerformanceHandler:
            def __init__(self):
                self.event_count = 0
                self.start_time = None
                self.end_time = None
            
            async def handle_event(self, event):
                if self.start_time is None:
                    self.start_time = asyncio.get_event_loop().time()
                self.event_count += 1
                self.end_time = asyncio.get_event_loop().time()
            
            async def handle_error(self, error, session_id):
                pass
        
        handler = PerformanceHandler()
        session.add_handler(handler)
        
        # 发送大量事件
        event_count = 1000
        for i in range(event_count):
            event = StreamEvent(
                event_type=StreamEventType.PROCESSING_STATUS,
                session_id="performance-test",
                data={"step": i}
            )
            await session.emit_event(event)
        
        # 验证性能
        assert handler.event_count == event_count
        total_time = handler.end_time - handler.start_time
        events_per_second = event_count / total_time
        
        # 验证性能指标（应该能处理大量事件）
        assert events_per_second > 100  # 每秒至少100个事件


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
