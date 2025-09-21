"""
Agent节点基类测试
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.base_node import (
    BaseAgentNode,
    SimpleAgentNode,
    node_error_handler
)
from utils.error_handler import ErrorSeverity, reset_error_handler


class TestBaseAgentNode:
    """BaseAgentNode 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()

    @pytest.mark.asyncio
    async def test_base_node_abstract_methods(self):
        """测试基类的抽象方法"""
        # BaseAgentNode是抽象类，不能直接实例化
        with pytest.raises(TypeError):
            BaseAgentNode()

    @pytest.mark.asyncio
    async def test_prep_async_success(self):
        """测试准备阶段成功执行"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True, "data": "test_data"}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        shared = {}
        
        with patch('agent.base_node.emit_processing_status') as mock_emit:
            result = await node.prep_async(shared)
        
        assert result["prepared"] is True
        assert result["data"] == "test_data"
        assert result["node_name"] == "test_node"
        assert "prep_start_time" in result
        assert "prep_duration" in result
        assert "timestamp" in result
        
        # 验证流式事件被发送
        mock_emit.assert_called()

    @pytest.mark.asyncio
    async def test_prep_async_error(self):
        """测试准备阶段错误处理"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                raise ValueError("Preparation failed")
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        shared = {}
        
        with patch('agent.base_node.emit_error') as mock_emit_error:
            result = await node.prep_async(shared)
        
        assert "error" in result
        assert result["error"] == "Preparation failed"
        assert result["error_type"] == "ValueError"
        assert result["node_name"] == "test_node"
        
        # 验证错误被记录到shared
        assert "errors" in shared
        assert len(shared["errors"]) == 1
        
        # 验证错误事件被发送
        mock_emit_error.assert_called_with(shared, "Preparation failed")

    @pytest.mark.asyncio
    async def test_exec_async_success(self):
        """测试执行阶段成功执行"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True, "result": "test_result"}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        prep_res = {"prepared": True, "node_name": "test_node"}
        
        result = await node.exec_async(prep_res)
        
        assert result["executed"] is True
        assert result["result"] == "test_result"
        assert result["node_name"] == "test_node"
        assert "exec_start_time" in result
        assert "exec_duration" in result

    @pytest.mark.asyncio
    async def test_exec_async_with_prep_error(self):
        """测试执行阶段处理准备阶段错误"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        prep_res = {"error": "Preparation failed"}
        
        result = await node.exec_async(prep_res)
        
        # 应该直接返回准备阶段的错误
        assert result == prep_res

    @pytest.mark.asyncio
    async def test_exec_async_error(self):
        """测试执行阶段错误处理"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                raise RuntimeError("Execution failed")
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        prep_res = {"prepared": True}
        
        result = await node.exec_async(prep_res)
        
        assert "error" in result
        assert "test_node节点执行失败" in result["error"]
        assert result["error_type"] == "RuntimeError"
        assert result["failed_stage"] == "execution"

    @pytest.mark.asyncio
    async def test_post_async_success(self):
        """测试后处理阶段成功执行"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                shared["result"] = "processed"
                return "success"
        
        node = TestNode("test_node")
        shared = {}
        prep_res = {"prepared": True}
        exec_res = {"executed": True}
        
        with patch('agent.base_node.emit_processing_status') as mock_emit:
            next_action = await node.post_async(shared, prep_res, exec_res)
        
        assert next_action == "success"
        assert shared["result"] == "processed"
        
        # 验证完成事件被发送
        mock_emit.assert_called()

    @pytest.mark.asyncio
    async def test_post_async_with_exec_error(self):
        """测试后处理阶段处理执行错误"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        shared = {}
        prep_res = {"prepared": True}
        exec_res = {"error": "Execution failed"}
        
        with patch('agent.base_node.emit_error') as mock_emit_error:
            next_action = await node.post_async(shared, prep_res, exec_res)
        
        assert next_action == "error"
        
        # 验证错误被记录
        assert "errors" in shared
        assert len(shared["errors"]) == 1
        
        # 验证错误事件被发送
        mock_emit_error.assert_called_with(shared, "Execution failed")

    @pytest.mark.asyncio
    async def test_post_async_error(self):
        """测试后处理阶段错误处理"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                raise ValueError("Post processing failed")
        
        node = TestNode("test_node")
        shared = {}
        prep_res = {"prepared": True}
        exec_res = {"executed": True}
        
        with patch('agent.base_node.emit_error') as mock_emit_error:
            next_action = await node.post_async(shared, prep_res, exec_res)
        
        assert next_action == "error"
        
        # 验证错误被记录
        assert "errors" in shared
        assert len(shared["errors"]) == 1
        
        # 验证错误事件被发送
        mock_emit_error.assert_called()

    def test_get_node_stats(self):
        """测试获取节点统计信息"""
        class TestNode(BaseAgentNode):
            async def _prep_impl(self, shared):
                return {"prepared": True}
            
            async def _exec_impl(self, prep_res):
                return {"executed": True}
            
            async def _post_impl(self, shared, prep_res, exec_res):
                return "success"
        
        node = TestNode("test_node")
        stats = node.get_node_stats()
        
        assert stats["node_name"] == "test_node"
        assert stats["node_type"] == "TestNode"
        assert "error_count" in stats


class TestSimpleAgentNode:
    """SimpleAgentNode 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()

    @pytest.mark.asyncio
    async def test_simple_node_default_implementation(self):
        """测试简单节点的默认实现"""
        class TestSimpleNode(SimpleAgentNode):
            async def _exec_impl(self, prep_res):
                return {"result": "simple_execution"}
        
        node = TestSimpleNode("simple_test")
        shared = {}
        
        # 测试默认的准备实现
        prep_res = await node.prep_async(shared)
        assert prep_res["ready"] is True
        
        # 测试自定义的执行实现
        exec_res = await node.exec_async(prep_res)
        assert exec_res["result"] == "simple_execution"
        
        # 测试默认的后处理实现
        next_action = await node.post_async(shared, prep_res, exec_res)
        assert next_action == "success"

    @pytest.mark.asyncio
    async def test_simple_node_missing_exec_impl(self):
        """测试简单节点缺少执行实现"""
        class IncompleteNode(SimpleAgentNode):
            pass  # 没有实现 _exec_impl
        
        node = IncompleteNode("incomplete")
        shared = {}
        
        prep_res = await node.prep_async(shared)
        
        # 执行阶段应该抛出 NotImplementedError
        exec_res = await node.exec_async(prep_res)
        assert "error" in exec_res
        assert "NotImplementedError" in exec_res["error_type"]


class TestNodeErrorHandlerDecorator:
    """节点错误处理装饰器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        reset_error_handler()

    @pytest.mark.asyncio
    async def test_node_error_handler_success(self):
        """测试节点错误处理装饰器成功情况"""
        @node_error_handler(severity=ErrorSeverity.LOW)
        async def test_method(shared):
            return {"success": True}
        
        shared = {}
        result = await test_method(shared)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_node_error_handler_error(self):
        """测试节点错误处理装饰器错误情况"""
        @node_error_handler(
            severity=ErrorSeverity.HIGH,
            user_message="测试操作失败"
        )
        async def test_method(shared):
            raise ValueError("Test error")
        
        shared = {}
        result = await test_method(shared)
        
        assert result["success"] is False
        assert result["fallback"] is True
        assert "error" in result
        
        # 验证错误被记录到shared
        assert "errors" in shared
        assert len(shared["errors"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
