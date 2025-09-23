"""
OpenAI客户端增强错误处理测试

测试增强的错误处理、重试机制和统计功能
"""
import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.openai_client import OpenAIClient, SimpleOpenAIConfig, RetryManager
from utils.openai_client import OpenAIClientError, OpenAIRateLimitError, OpenAITimeoutError


def test_retry_manager_config_merging():
    """测试重试管理器配置合并功能"""
    # 测试默认配置
    manager = RetryManager()
    assert "max_retries_by_error_type" in manager.retry_config
    assert manager.retry_config["max_retries_by_error_type"]["rate_limit"] == 5
    
    # 测试自定义配置合并
    custom_config = {
        "max_retries_by_error_type": {
            "rate_limit": 10,
            "new_error_type": 3
        },
        "max_delay": 120.0
    }
    
    manager = RetryManager(retry_config=custom_config)
    assert manager.retry_config["max_retries_by_error_type"]["rate_limit"] == 10
    assert manager.retry_config["max_retries_by_error_type"]["timeout"] == 3  # 保持默认
    assert manager.retry_config["max_delay"] == 120.0
    assert "new_error_type" in manager.retry_config["max_retries_by_error_type"]


def test_error_classification():
    """测试错误分类功能"""
    manager = RetryManager()
    
    # 测试速率限制错误分类
    rate_limit_error = Exception("Rate limit exceeded")
    assert manager._classify_error_type(rate_limit_error) == "rate_limit"
    
    # 测试超时错误分类
    timeout_error = Exception("Request timed out")
    assert manager._classify_error_type(timeout_error) == "timeout"
    
    # 测试网络错误分类
    network_error = Exception("Network connection failed")
    assert manager._classify_error_type(network_error) == "network"
    
    # 测试默认错误分类
    unknown_error = Exception("Some unknown error")
    assert manager._classify_error_type(unknown_error) == "default"


def test_retry_decision_logic():
    """测试重试决策逻辑"""
    manager = RetryManager(max_retries=3)
    
    # 测试速率限制错误的重试决策
    rate_limit_error = Exception("rate limit")
    assert manager._should_retry(rate_limit_error, 0) == True
    assert manager._should_retry(rate_limit_error, 4) == True   # 速率限制错误最大重试5次
    assert manager._should_retry(rate_limit_error, 5) == False  # 超过最大重试次数
    
    # 测试默认错误的重试决策
    unknown_error = Exception("unknown")
    assert manager._should_retry(unknown_error, 2) == True
    assert manager._should_retry(unknown_error, 3) == False


def test_delay_calculation():
    """测试延迟计算功能"""
    manager = RetryManager(base_delay=1.0)
    
    # 测试基础延迟计算
    delay = manager._calculate_delay(0, "default")
    assert 0.1 <= delay <= 2.5  # 考虑抖动范围
    
    # 测试指数退避
    delay1 = manager._calculate_delay(1, "default")
    delay2 = manager._calculate_delay(2, "default")
    assert delay2 > delay1  # 指数增长
    
    # 测试最大延迟限制
    manager.retry_config["max_delay"] = 5.0
    delay = manager._calculate_delay(10, "default")  # 很大的尝试次数
    assert delay <= 5.0


def test_user_friendly_error_messages():
    """测试用户友好的错误消息生成"""
    config = SimpleOpenAIConfig(api_key="test_key")
    client = OpenAIClient(config)
    
    # 测试速率限制错误消息
    rate_limit_error = OpenAIRateLimitError("Rate limit exceeded")
    message = client._get_user_friendly_error_message(rate_limit_error)
    assert "API访问频率受限" in message
    assert "稍后再试" in message
    
    # 测试超时错误消息
    timeout_error = OpenAITimeoutError("Request timeout")
    message = client._get_user_friendly_error_message(timeout_error)
    assert "请求超时" in message
    assert "网络连接" in message
    
    # 测试默认错误消息
    unknown_error = OpenAIClientError("Unknown error")
    message = client._get_user_friendly_error_message(unknown_error)
    assert "未知错误" in message
    assert "重试" in message


def test_error_statistics_tracking():
    """测试错误统计跟踪功能"""
    config = SimpleOpenAIConfig(api_key="test_key")
    client = OpenAIClient(config)
    
    # 重置统计
    client.reset_stats()
    
    # 模拟各种错误
    errors = [
        OpenAIRateLimitError("rate limit"),
        OpenAITimeoutError("timeout"),
        OpenAIClientError("unknown", error_type="bad_request")
    ]
    
    for error in errors:
        client._update_failure_stats(error)
    
    stats = client.get_stats()
    assert stats["failed_requests"] == 3
    assert stats["error_stats"]["rate_limit"] == 1
    assert stats["error_stats"]["timeout"] == 1
    assert stats["error_stats"]["bad_request"] == 1


def test_latency_statistics():
    """测试延迟统计功能"""
    config = SimpleOpenAIConfig(api_key="test_key")
    client = OpenAIClient(config)
    
    # 重置统计
    client.reset_stats()
    
    # 模拟多个延迟值
    latencies = [0.5, 1.2, 0.8, 2.1, 1.5]
    
    for latency in latencies:
        client._update_latency_stats(latency)
    
    stats = client.get_stats()["latency_stats"]
    assert stats["min"] == 0.5
    assert stats["max"] == 2.1
    assert abs(stats["avg"] - sum(latencies) / len(latencies)) < 0.01
    assert stats["total_count"] == 5


@patch('utils.openai_client.AsyncOpenAI')
def test_api_call_with_retry(mock_async_openai):
    """测试带重试的API调用"""
    # 模拟API客户端
    mock_client = AsyncMock()
    mock_async_openai.return_value = mock_client
    
    # 配置第一次失败，第二次成功
    mock_client.chat.completions.create.side_effect = [
        Exception("rate limit exceeded"),
        MagicMock()  # 成功响应
    ]
    
    config = SimpleOpenAIConfig(api_key="test_key", max_retries=3)
    client = OpenAIClient(config)
    
    # 执行测试
    async def test_call():
        return await client.retry_manager.execute_with_retry(
            mock_client.chat.completions.create,
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}]
        )
    
    # 应该成功（重试后）
    result = asyncio.run(test_call())
    assert result is not None
    assert mock_client.chat.completions.create.call_count == 2


def test_safe_request_info():
    """测试安全的请求信息处理"""
    config = SimpleOpenAIConfig(api_key="test_key")
    client = OpenAIClient(config)
    
    # 包含敏感信息的请求
    sensitive_request = {
        "api_key": "secret_key_123",
        "messages": [{"role": "user", "content": "test"}],
        "password": "should_be_redacted"
    }
    
    safe_info = client._prepare_safe_request_info(sensitive_request)
    
    # 验证敏感信息被隐藏
    assert safe_info["api_key"] == "[REDACTED]"
    assert safe_info["password"] == "[REDACTED]"
    assert safe_info["messages"][0]["content"] == "test"  # 非敏感信息保留


if __name__ == "__main__":
    pytest.main([__file__, "-v"])