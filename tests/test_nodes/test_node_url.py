"""
NodeURL 节点单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from agent.nodes.node_url import NodeURL


@pytest.fixture
def mock_web_client():
    """创建一个模拟的 JinaWebClient"""
    with patch('agent.nodes.node_url.JinaWebClient') as mock_client:
        client_instance = AsyncMock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def node_url(mock_web_client):
    """创建 NodeURL 实例"""
    node = NodeURL()
    node.web_client = mock_web_client
    node.client_available = True
    return node


@pytest.mark.asyncio
async def test_prep_async_with_url():
    """测试 prep_async 方法 - 提供URL"""
    node = NodeURL()
    
    # 准备共享状态
    shared = {
        "url": "https://example.com",
        "extraction_type": "full",
        "max_content_length": 5000
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "url" in result
    assert result["url"] == "https://example.com"
    assert result["extraction_type"] == "full"
    assert result["max_content_length"] == 5000
    assert "parsed_url" in result


@pytest.mark.asyncio
async def test_prep_async_with_first_search_result():
    """测试 prep_async 方法 - 从first_search_result获取URL"""
    node = NodeURL()
    
    # 准备共享状态
    shared = {
        "first_search_result": {
            "url": "https://example.com/search-result"
        },
        "extraction_type": "full",
        "max_content_length": 5000
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "url" in result
    assert result["url"] == "https://example.com/search-result"
    assert result["extraction_type"] == "full"
    assert result["max_content_length"] == 5000


@pytest.mark.asyncio
async def test_prep_async_without_url():
    """测试 prep_async 方法 - 没有URL"""
    node = NodeURL()
    
    # 准备共享状态
    shared = {
        "extraction_type": "full",
        "max_content_length": 5000
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "error" in result
    assert "No URL provided" in result["error"]


@pytest.mark.asyncio
async def test_prep_async_invalid_url():
    """测试 prep_async 方法 - 无效URL"""
    node = NodeURL()
    
    # 准备共享状态
    shared = {
        "url": "invalid-url",
        "extraction_type": "full",
        "max_content_length": 5000
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "error" in result
    assert "Invalid URL format" in result["error"]


@pytest.mark.asyncio
async def test_exec_async_success(node_url):
    """测试 exec_async 方法 - 成功情况"""
    # 设置模拟网页信息
    mock_page_info = {
        "title": "示例网页",
        "description": "这是一个示例网页",
        "url": "https://example.com",
        "content": "这是网页的内容"
    }
    
    node_url.web_client.get_page_info = AsyncMock(return_value=mock_page_info)
    
    # 准备参数
    prep_res = {
        "url": "https://example.com",
        "max_content_length": 10000
    }
    
    # 执行URL解析
    result = await node_url.exec_async(prep_res)
    
    # 验证结果
    assert "url" in result
    assert result["url"] == "https://example.com"
    assert result["title"] == "示例网页"
    assert result["content"] == "这是网页的内容"
    assert result["processing_status"] == "success"
    assert "metadata" in result
    assert "extracted_sections" in result


@pytest.mark.asyncio
async def test_exec_async_content_truncation(node_url):
    """测试 exec_async 方法 - 内容截断"""
    # 创建长内容
    long_content = "A" * 15000  # 15000个字符
    
    # 设置模拟网页信息
    mock_page_info = {
        "title": "长内容网页",
        "description": "这是一个长内容网页",
        "url": "https://example.com/long",
        "content": long_content
    }
    
    node_url.web_client.get_page_info = AsyncMock(return_value=mock_page_info)
    
    # 准备参数（限制内容长度为10000）
    prep_res = {
        "url": "https://example.com/long",
        "max_content_length": 10000
    }
    
    # 执行URL解析
    result = await node_url.exec_async(prep_res)
    
    # 验证结果
    assert "content" in result
    # 验证内容被截断并在末尾添加了"..."
    assert len(result["content"]) == 10003  # 10000 + "..."
    assert result["content"].endswith("...")


@pytest.mark.asyncio
async def test_exec_async_client_not_available():
    """测试 exec_async 方法 - 客户端不可用"""
    node = NodeURL()
    node.web_client = None
    node.client_available = False
    
    # 准备参数
    prep_res = {
        "url": "https://example.com",
        "max_content_length": 10000
    }
    
    # 执行URL解析并验证异常
    with pytest.raises(RuntimeError, match="Web API not configured"):
        await node.exec_async(prep_res)


@pytest.mark.asyncio
async def test_post_async_success():
    """测试 post_async 方法 - 成功情况"""
    node = NodeURL()
    
    # 准备共享状态、准备结果和执行结果
    shared = {}
    prep_res = {}
    exec_res = {
        "url": "https://example.com",
        "title": "示例网页",
        "content": "这是网页的内容",
        "metadata": {
            "author": "",
            "publish_date": "",
            "tags": [],
            "description": "网页描述"
        },
        "extracted_sections": [],
        "processing_status": "success",
        "processing_time": 100
    }
    
    # 执行后处理
    result = await node.post_async(shared, prep_res, exec_res)
    
    # 验证结果
    assert result == "url_parsed"
    assert "url_content" in shared
    assert shared["url_content"] == "这是网页的内容"
    assert "url_title" in shared
    assert shared["url_title"] == "示例网页"
    assert "url_metadata" in shared
    assert shared["url_metadata"]["description"] == "网页描述"


@pytest.mark.asyncio
async def test_post_async_with_error():
    """测试 post_async 方法 - 错误情况"""
    node = NodeURL()
    
    # 准备共享状态、准备结果和执行结果
    shared = {}
    prep_res = {}
    exec_res = {
        "error": "URL解析失败"
    }
    
    # 执行后处理
    result = await node.post_async(shared, prep_res, exec_res)
    
    # 验证结果
    assert result == "error"
    assert "errors" in shared
    assert len(shared["errors"]) == 1
    assert shared["errors"][0]["source"] == "NodeURL.exec"
    assert shared["errors"][0]["error"] == "URL解析失败"


@pytest.mark.asyncio
async def test_exec_fallback():
    """测试 exec_fallback 方法"""
    node = NodeURL()
    
    # 准备参数
    prep_res = {
        "url": "https://example.com"
    }
    exception = Exception("网络错误")
    
    # 执行降级处理
    result = node.exec_fallback(prep_res, exception)
    
    # 验证结果
    assert "error" in result
    assert "URL parsing failed for https://example.com" in result["error"]
    assert "网络错误" in result["error"]
    assert result["url"] == "https://example.com"
    assert result["processing_status"] == "failed"


def test_create_error_result():
    """测试 _create_error_result 方法"""
    node = NodeURL()
    
    # 执行创建错误结果
    result = node._create_error_result("测试错误", "https://example.com", "full")
    
    # 验证结果
    assert "error" in result
    assert result["error"] == "测试错误"
    assert result["url"] == "https://example.com"
    assert result["extraction_type"] == "full"
    assert "target_selectors" in result
    assert "max_content_length" in result


if __name__ == "__main__":
    pytest.main([__file__])