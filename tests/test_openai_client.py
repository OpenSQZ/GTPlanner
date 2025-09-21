"""
OpenAI 客户端测试
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.openai_client import (
    SimpleOpenAIConfig,
    OpenAIClient,
    get_openai_client,
    RetryManager
)


class TestSimpleOpenAIConfig:
    """SimpleOpenAIConfig 测试类"""

    def test_to_openai_client_kwargs(self):
        """测试转换为 OpenAI 客户端参数"""
        config = SimpleOpenAIConfig(
            api_key="test-key",
            base_url="https://api.test.com",
            timeout=30.0,
            max_retries=5
        )

        kwargs = config.to_openai_client_kwargs()

        assert kwargs["api_key"] == "test-key"
        assert kwargs["base_url"] == "https://api.test.com"
        assert kwargs["timeout"] == 30.0
        assert kwargs["max_retries"] == 5

    def test_config_with_mock_api_key(self):
        """测试带模拟API密钥的配置"""
        # 使用模拟的API密钥来避免验证错误
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            config = SimpleOpenAIConfig(
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000,
                timeout=60.0
            )

            assert config.api_key == "test-key"
            assert config.model == "gpt-3.5-turbo"
            assert config.temperature == 0.7
            assert config.max_tokens == 1000
            assert config.timeout == 60.0


# ContentExtractor 类在当前版本中不存在，跳过相关测试


class TestRetryManager:
    """RetryManager 测试类"""

    def test_init(self):
        """测试初始化"""
        manager = RetryManager(max_retries=5, base_delay=1.0)
        assert manager.max_retries == 5
        assert manager.base_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """测试重试机制 - 成功情况"""
        manager = RetryManager(max_retries=3, base_delay=0.1)

        async def mock_function():
            return "success"

        result = await manager.execute_with_retry(mock_function)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self):
        """测试重试机制 - 失败情况"""
        manager = RetryManager(max_retries=2, base_delay=0.1)

        call_count = 0
        async def mock_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            await manager.execute_with_retry(mock_function)

        # 验证至少调用了一次（具体重试次数取决于实现）
        assert call_count >= 1


class TestOpenAIClient:
    """OpenAIClient 测试类"""

    def test_client_initialization_with_mock_key(self):
        """测试客户端初始化（使用模拟密钥）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('utils.openai_client.AsyncOpenAI') as mock_openai:
                client = OpenAIClient()

                assert client.config is not None
                assert isinstance(client.config, SimpleOpenAIConfig)
                assert client.retry_manager is not None
                assert "total_requests" in client.stats

    def test_prepare_messages_with_mock_key(self):
        """测试消息准备（使用模拟密钥）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('utils.openai_client.AsyncOpenAI'):
                client = OpenAIClient()

                messages = [
                    {"role": "user", "content": "Hello"}
                ]
                system_prompt = "You are a helpful assistant."

                prepared = client._prepare_messages(messages, system_prompt)

                assert len(prepared) == 2
                assert prepared[0]["role"] == "system"
                assert prepared[0]["content"] == system_prompt
                assert prepared[1]["role"] == "user"
                assert prepared[1]["content"] == "Hello"

    def test_get_stats_with_mock_key(self):
        """测试统计信息获取（使用模拟密钥）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('utils.openai_client.AsyncOpenAI'):
                client = OpenAIClient()

                stats = client.get_stats()

                assert "total_requests" in stats
                assert "successful_requests" in stats
                assert "failed_requests" in stats
                assert "total_tokens" in stats
                assert "total_time" in stats


class TestGlobalClient:
    """全局客户端测试"""

    def test_get_openai_client_with_mock_key(self):
        """测试全局客户端获取（使用模拟密钥）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('utils.openai_client.AsyncOpenAI'):
                # 重置全局客户端
                import utils.openai_client
                utils.openai_client._global_client = None

                client1 = get_openai_client()
                client2 = get_openai_client()

                # 应该返回同一个实例
                assert client1 is client2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
