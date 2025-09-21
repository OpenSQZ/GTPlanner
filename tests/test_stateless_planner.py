"""
StatelessGTPlanner 核心功能测试
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# 添加项目根目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, AgentResult, create_user_message
from agent.streaming.stream_interface import StreamingSession


class TestStatelessGTPlanner:
    """StatelessGTPlanner 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.planner = StatelessGTPlanner()

    def test_init(self):
        """测试初始化"""
        planner = StatelessGTPlanner()
        assert planner is not None
        # 验证无状态特性：不应该有实例变量
        assert not hasattr(planner, 'state') or planner.__dict__ == {}

    @pytest.mark.asyncio
    async def test_process_basic_input(self):
        """测试基本输入处理"""
        # 创建测试上下文
        context = AgentContext(
            session_id="test-session-001",
            dialogue_history=[create_user_message("测试需求：设计一个简单的用户管理系统")],
            tool_execution_results={},
            session_metadata={}
        )
        
        # 创建模拟的流式会话
        mock_streaming_session = Mock(spec=StreamingSession)
        mock_streaming_session.session_id = "test-session-001"
        mock_streaming_session.emit_event = AsyncMock()
        
        # 模拟 PocketFlowSharedFactory 和 ReActOrchestratorFlow
        with patch('agent.stateless_planner.PocketFlowSharedFactory') as mock_factory, \
             patch('agent.stateless_planner.ReActOrchestratorFlow') as mock_orchestrator_class:
            
            # 设置模拟工厂
            mock_shared = {
                "user_requirements": "测试需求：设计一个简单的用户管理系统",
                "dialogue_history": {"messages": [{"role": "user", "content": "测试需求：设计一个简单的用户管理系统"}]},
                "new_messages": [{"role": "assistant", "content": "我将帮您设计用户管理系统"}],
                "tool_execution_results": {}
            }
            mock_factory.create_shared_dict.return_value = mock_shared
            mock_factory.create_agent_result.return_value = AgentResult(
                success=True,
                new_messages=[{"role": "assistant", "content": "我将帮您设计用户管理系统"}],
                tool_execution_results_updates={},
                metadata={"test": True},
                execution_time=0.5
            )
            
            # 设置模拟编排器
            mock_orchestrator = Mock()
            mock_orchestrator.run_async = AsyncMock(return_value="success")
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # 执行测试
            result = await self.planner.process(
                user_input="测试需求：设计一个简单的用户管理系统",
                context=context,
                streaming_session=mock_streaming_session
            )
            
            # 验证结果
            assert isinstance(result, AgentResult)
            assert result.success is True
            assert len(result.new_messages) > 0
            assert result.execution_time >= 0
            
            # 验证工厂方法被调用
            mock_factory.create_shared_dict.assert_called_once()
            mock_factory.create_agent_result.assert_called_once()
            
            # 验证编排器被调用
            mock_orchestrator.run_async.assert_called_once()
            
            # 验证流式事件被发送
            assert mock_streaming_session.emit_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_process_with_error(self):
        """测试错误处理"""
        context = AgentContext(
            session_id="test-session-error",
            dialogue_history=[create_user_message("测试错误情况")],
            tool_execution_results={},
            session_metadata={}
        )
        
        mock_streaming_session = Mock(spec=StreamingSession)
        mock_streaming_session.session_id = "test-session-error"
        mock_streaming_session.emit_event = AsyncMock()
        
        # 模拟处理过程中的异常
        with patch('agent.stateless_planner.PocketFlowSharedFactory') as mock_factory:
            mock_factory.create_shared_dict.side_effect = Exception("模拟错误")
            
            result = await self.planner.process(
                user_input="测试错误情况",
                context=context,
                streaming_session=mock_streaming_session
            )
            
            # 验证错误结果
            assert isinstance(result, AgentResult)
            assert result.success is False
            assert "Processing failed" in result.error
            assert result.metadata["error_type"] == "Exception"
            assert result.execution_time >= 0
            
            # 验证错误事件被发送
            mock_streaming_session.emit_event.assert_called()

    @pytest.mark.asyncio
    async def test_process_with_language(self):
        """测试语言参数传递"""
        context = AgentContext(
            session_id="test-session-lang",
            dialogue_history=[create_user_message("Design a user management system")],
            tool_execution_results={},
            session_metadata={}
        )
        
        mock_streaming_session = Mock(spec=StreamingSession)
        mock_streaming_session.session_id = "test-session-lang"
        mock_streaming_session.emit_event = AsyncMock()
        
        with patch('agent.stateless_planner.PocketFlowSharedFactory') as mock_factory, \
             patch('agent.stateless_planner.ReActOrchestratorFlow') as mock_orchestrator_class:
            
            mock_shared = {"test": "data"}
            mock_factory.create_shared_dict.return_value = mock_shared
            mock_factory.create_agent_result.return_value = AgentResult(
                success=True,
                new_messages=[],
                tool_execution_results_updates={},
                metadata={},
                execution_time=0.1
            )
            
            mock_orchestrator = Mock()
            mock_orchestrator.run_async = AsyncMock(return_value="success")
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # 测试英文语言参数
            await self.planner.process(
                user_input="Design a user management system",
                context=context,
                streaming_session=mock_streaming_session,
                language="en"
            )
            
            # 验证语言参数被传递给工厂
            mock_factory.create_shared_dict.assert_called_with(
                "Design a user management system", 
                context, 
                language="en"
            )

    def test_streaming_callbacks_exist(self):
        """测试流式回调方法存在"""
        # 验证所有必需的回调方法都存在
        assert hasattr(StatelessGTPlanner, '_on_llm_start')
        assert hasattr(StatelessGTPlanner, '_on_llm_chunk')
        assert hasattr(StatelessGTPlanner, '_on_llm_end')
        assert hasattr(StatelessGTPlanner, '_on_tool_start')
        assert hasattr(StatelessGTPlanner, '_on_tool_progress')
        assert hasattr(StatelessGTPlanner, '_on_tool_end')
        
        # 验证这些都是静态方法或类方法
        import inspect
        assert inspect.iscoroutinefunction(StatelessGTPlanner._on_llm_start)
        assert inspect.iscoroutinefunction(StatelessGTPlanner._on_llm_chunk)
        assert inspect.iscoroutinefunction(StatelessGTPlanner._on_llm_end)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
