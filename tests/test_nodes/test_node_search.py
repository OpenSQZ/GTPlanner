"""
NodeSearch 节点单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from agent.nodes.node_search import NodeSearch


@pytest.fixture
def mock_search_client():
    """创建一个模拟的 JinaSearchClient"""
    with patch('agent.nodes.node_search.JinaSearchClient') as mock_client:
        client_instance = AsyncMock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def node_search(mock_search_client):
    """创建 NodeSearch 实例"""
    node = NodeSearch()
    node.search_client = mock_search_client
    node.search_available = True
    return node


@pytest.mark.asyncio
async def test_prep_async_with_current_keyword():
    """测试 prep_async 方法 - 使用 current_keyword"""
    node = NodeSearch()
    
    # 准备共享状态
    shared = {
        "current_keyword": "Python编程",
        "search_type": "web",
        "max_results": 5,
        "language": "zh-CN"
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "search_keywords" in result
    assert result["search_keywords"] == ["Python编程"]
    assert result["search_type"] == "web"
    assert result["max_results"] == 5
    assert result["language"] == "zh-CN"


@pytest.mark.asyncio
async def test_prep_async_with_search_keywords():
    """测试 prep_async 方法 - 使用 search_keywords"""
    node = NodeSearch()
    
    # 准备共享状态
    shared = {
        "search_keywords": ["Python", "编程", "教程"],
        "search_type": "web",
        "max_results": 10,
        "language": "zh-CN"
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "search_keywords" in result
    assert result["search_keywords"] == ["Python", "编程", "教程"]
    assert result["search_type"] == "web"
    assert result["max_results"] == 10
    assert result["language"] == "zh-CN"


@pytest.mark.asyncio
async def test_prep_async_without_keywords():
    """测试 prep_async 方法 - 没有关键词"""
    node = NodeSearch()
    
    # 准备共享状态
    shared = {
        "search_type": "web",
        "max_results": 10,
        "language": "zh-CN"
    }
    
    # 执行准备阶段
    result = await node.prep_async(shared)
    
    # 验证结果
    assert "error" in result
    assert "No search keywords provided" in result["error"]


@pytest.mark.asyncio
async def test_exec_async_success(node_search):
    """测试 exec_async 方法 - 成功情况"""
    # 设置模拟搜索结果
    mock_results = [
        {
            "title": "Python编程入门",
            "url": "https://example.com/python1",
            "description": "Python编程教程",
            "content": "Python是一种编程语言"
        },
        {
            "title": "Python高级编程",
            "url": "https://example.com/python2",
            "description": "Python高级教程",
            "content": "Python高级特性"
        }
    ]
    
    node_search.search_client.search_simple = AsyncMock(return_value=mock_results)
    
    # 准备参数
    prep_res = {
        "search_keywords": ["Python"],
        "max_results": 5
    }
    
    # 执行搜索
    result = await node_search.exec_async(prep_res)
    
    # 验证结果
    assert "search_results" in result
    assert len(result["search_results"]) == 2
    assert result["search_results"][0]["title"] == "Python编程入门"
    assert result["search_results"][1]["title"] == "Python高级编程"
    assert result["total_found"] == 2


@pytest.mark.asyncio
async def test_exec_async_with_deduplication(node_search):
    """测试 exec_async 方法 - 去重功能"""
    # 设置模拟搜索结果（包含重复URL）
    mock_results = [
        {
            "title": "Python编程入门",
            "url": "https://example.com/python",
            "description": "Python编程教程",
            "content": "Python是一种编程语言"
        },
        {
            "title": "Python编程进阶",
            "url": "https://example.com/python",  # 重复URL
            "description": "Python进阶教程",
            "content": "Python进阶特性"
        },
        {
            "title": "Python高级编程",
            "url": "https://example.com/python-advanced",
            "description": "Python高级教程",
            "content": "Python高级特性"
        }
    ]
    
    node_search.search_client.search_simple = AsyncMock(return_value=mock_results)
    
    # 准备参数
    prep_res = {
        "search_keywords": ["Python"],
        "max_results": 5
    }
    
    # 执行搜索
    result = await node_search.exec_async(prep_res)
    
    # 验证去重结果
    assert "search_results" in result
    assert len(result["search_results"]) == 2  # 应该只有2个不重复的结果
    assert result["total_found"] == 2
    # 验证第一个结果被保留
    assert result["search_results"][0]["url"] == "https://example.com/python"
    # 验证第三个结果被保留
    assert result["search_results"][1]["url"] == "https://example.com/python-advanced"


@pytest.mark.asyncio
async def test_exec_async_empty_keywords():
    """测试 exec_async 方法 - 空关键词"""
    node = NodeSearch()
    
    # 准备参数
    prep_res = {
        "search_keywords": [],
        "max_results": 5
    }
    
    # 执行搜索并验证异常
    with pytest.raises(ValueError, match="Empty search keywords"):
        await node.exec_async(prep_res)


@pytest.mark.asyncio
async def test_post_async_success():
    """测试 post_async 方法 - 成功情况"""
    node = NodeSearch()
    
    # 准备共享状态和执行结果
    shared = {}
    prep_res = {}
    exec_res = {
        "search_results": [
            {
                "title": "Python编程入门",
                "url": "https://example.com/python1",
                "snippet": "Python编程教程",
                "content": "Python是一种编程语言"
            }
        ]
    }
    
    # 执行后处理
    result = await node.post_async(shared, prep_res, exec_res)
    
    # 验证结果
    assert result == "search_complete"
    assert "first_search_result" in shared
    assert "all_search_results" in shared
    assert shared["first_search_result"]["title"] == "Python编程入门"
    assert len(shared["all_search_results"]) == 1


@pytest.mark.asyncio
async def test_post_async_with_error():
    """测试 post_async 方法 - 错误情况"""
    node = NodeSearch()
    
    # 准备共享状态和执行结果
    shared = {}
    prep_res = {}
    exec_res = {
        "error": "搜索失败"
    }
    
    # 执行后处理
    result = await node.post_async(shared, prep_res, exec_res)
    
    # 验证结果
    assert result == "error"
    assert "errors" in shared
    assert len(shared["errors"]) == 1
    assert shared["errors"][0]["source"] == "NodeSearch.exec"
    assert shared["errors"][0]["error"] == "搜索失败"


def test_deduplicate_results():
    """测试 _deduplicate_results 方法"""
    node = NodeSearch()
    
    # 准备测试数据
    results = [
        {"url": "https://example.com/1", "title": "结果1"},
        {"url": "https://example.com/2", "title": "结果2"},
        {"url": "https://example.com/1", "title": "重复结果1"},  # 重复URL
        {"url": "https://example.com/3", "title": "结果3"},
        {"url": "https://example.com/2", "title": "重复结果2"},  # 重复URL
    ]
    
    # 执行去重
    deduplicated = node._deduplicate_results(results)
    
    # 验证结果
    assert len(deduplicated) == 3
    # 验证去重后的URL是唯一的
    urls = [result["url"] for result in deduplicated]
    assert len(set(urls)) == len(urls)
    # 验证第一个出现的结果被保留
    assert deduplicated[0]["title"] == "结果1"
    assert deduplicated[1]["title"] == "结果2"
    assert deduplicated[2]["title"] == "结果3"


if __name__ == "__main__":
    pytest.main([__file__])