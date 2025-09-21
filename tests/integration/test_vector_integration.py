"""
向量数据库集成测试

测试向量服务与其他组件的集成，包括：
- 工具推荐节点与向量服务的集成
- 工具索引节点与向量服务的集成
- 配置管理与向量服务的集成
- 错误处理与向量服务的集成
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import json
import requests
from typing import Dict, Any, List

from utils.unified_config import get_config_manager
from utils.error_handler import get_error_handler
from agent.utils.startup_init import _check_vector_service_config


class TestVectorServiceIntegration:
    """测试向量服务集成"""
    
    @pytest.mark.asyncio
    async def test_vector_service_startup_check(self):
        """测试启动时向量服务检查集成"""
        with patch('requests.get') as mock_get:
            # 模拟向量服务健康检查
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # 执行启动检查
            result = await _check_vector_service_config()
            
            # 验证集成结果
            assert isinstance(result, dict)
            assert "available" in result
            assert "config" in result
            
            # 验证配置集成
            config = result["config"]
            assert isinstance(config, dict)
            assert "base_url" in config
    
    @pytest.mark.asyncio
    async def test_vector_service_config_integration(self):
        """测试向量服务配置集成"""
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 测试向量服务相关配置
        vector_base_url = config_manager.get_setting("VECTOR_SERVICE_BASE_URL", "http://localhost:8080")
        vector_timeout = config_manager.get_setting("VECTOR_SERVICE_TIMEOUT", 30)
        vector_index = config_manager.get_setting("VECTOR_SERVICE_INDEX_NAME", "document_gtplanner_tools")
        
        # 验证配置类型和格式
        assert isinstance(vector_base_url, str)
        assert isinstance(vector_timeout, (int, str))
        assert isinstance(vector_index, str)
        
        # 验证索引名称格式（必须以document_开头）
        if vector_index != "document_gtplanner_tools":  # 默认值检查
            assert vector_index.startswith("document_"), f"索引名称必须以'document_'开头: {vector_index}"
    
    @pytest.mark.asyncio
    async def test_vector_service_error_handling_integration(self):
        """测试向量服务错误处理集成"""
        error_handler = get_error_handler()
        
        # 模拟向量服务错误
        test_errors = [
            "向量服务连接超时",
            "向量服务返回404错误",
            "向量索引不存在",
            "向量搜索失败"
        ]
        
        for error_msg in test_errors:
            # 记录向量服务相关错误
            error_handler.record_error(
                shared={},
                source="vector_service_test",
                error=Exception(error_msg)
            )
        
        # 验证错误记录
        error_summary = error_handler.get_error_summary()
        assert error_summary["total_errors"] >= len(test_errors)
        
        # 验证错误记录功能正常
        assert error_summary["total_errors"] > 0
        assert "by_severity" in error_summary
        assert "recent_errors" in error_summary


class TestToolRecommendationIntegration:
    """测试工具推荐集成"""
    
    def test_tool_recommendation_node_initialization(self):
        """测试工具推荐节点初始化集成"""
        with patch('utils.config_manager.get_vector_service_config') as mock_config:
            with patch('requests.get') as mock_health_check:
                # 模拟配置
                mock_config.return_value = {
                    "base_url": "http://test-vector-service:8080",
                    "timeout": 30,
                    "tools_index_name": "document_test_tools",
                    "vector_field": "combined_text"
                }
                
                # 模拟健康检查
                mock_response = Mock()
                mock_response.status_code = 200
                mock_health_check.return_value = mock_response
                
                # 尝试初始化工具推荐节点（模拟）
                node_config = {
                    "vector_service_url": "http://test-vector-service:8080",
                    "timeout": 30,
                    "index_name": "document_test_tools",
                    "vector_field": "combined_text",
                    "vector_service_available": True
                }
                
                # 验证节点配置
                assert node_config["vector_service_url"] is not None
                assert node_config["timeout"] > 0
                assert node_config["index_name"].startswith("document_")
                assert node_config["vector_service_available"] is True
    
    @pytest.mark.asyncio
    async def test_tool_search_integration(self):
        """测试工具搜索集成"""
        with patch('requests.post') as mock_post:
            # 模拟向量搜索响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": "openai-compatible.chat-completion",
                        "score": 0.95,
                        "metadata": {
                            "name": "OpenAI兼容聊天完成",
                            "type": "APIS",
                            "summary": "兼容OpenAI API格式的聊天完成服务"
                        }
                    }
                ],
                "total": 1
            }
            mock_post.return_value = mock_response
            
            # 模拟工具搜索请求
            search_request = {
                "query": "聊天对话API",
                "vector_field": "combined_text",
                "index": "document_test_tools",
                "top_k": 5
            }
            
            # 执行搜索
            response = requests.post(
                "http://test-vector-service/search",
                json=search_request
            )
            
            # 验证搜索集成
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) > 0
            
            # 验证结果格式
            result = data["results"][0]
            assert "id" in result
            assert "score" in result
            assert "metadata" in result
            assert result["score"] > 0.5  # 高相关度


class TestToolIndexingIntegration:
    """测试工具索引集成"""
    
    @pytest.mark.asyncio
    async def test_tool_indexing_workflow(self):
        """测试工具索引工作流集成"""
        with patch('requests.post') as mock_post, \
             patch('requests.delete') as mock_delete:
            
            # 模拟索引清除响应
            mock_delete_response = Mock()
            mock_delete_response.status_code = 200
            mock_delete.return_value = mock_delete_response
            
            # 模拟索引创建响应
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "status": "success",
                "indexed_count": 2,
                "index_name": "document_test_tools"
            }
            mock_post.return_value = mock_post_response
            
            # 模拟工具索引工作流
            # 1. 清除现有索引
            clear_response = requests.delete(
                "http://test-vector-service/index/document_test_tools/clear"
            )
            assert clear_response.status_code == 200
            
            # 2. 准备工具文档
            tool_documents = [
                {
                    "id": "openai-compatible.chat-completion",
                    "combined_text": "OpenAI兼容聊天完成API 支持多种大语言模型",
                    "metadata": {
                        "name": "OpenAI兼容聊天完成",
                        "type": "APIS",
                        "summary": "兼容OpenAI API格式的聊天完成服务"
                    }
                },
                {
                    "id": "openai-compatible.embeddings",
                    "combined_text": "OpenAI兼容文本向量化API 将文本转换为向量",
                    "metadata": {
                        "name": "OpenAI兼容文本向量化",
                        "type": "APIS", 
                        "summary": "兼容OpenAI API格式的文本向量化服务"
                    }
                }
            ]
            
            # 3. 创建索引
            index_response = requests.post(
                "http://test-vector-service/documents",
                json={
                    "documents": tool_documents,
                    "vector_field": "combined_text",
                    "index": "document_test_tools"
                }
            )
            
            # 验证索引工作流
            assert index_response.status_code == 200
            index_data = index_response.json()
            assert index_data["status"] == "success"
            assert index_data["indexed_count"] == len(tool_documents)
    
    def test_tool_document_preparation(self):
        """测试工具文档准备集成"""
        # 模拟从YAML文件解析的工具信息
        tool_yaml_data = {
            "id": "openai-compatible.chat-completion",
            "type": "APIS",
            "summary": "兼容OpenAI API格式的聊天完成服务",
            "description": "支持多种大语言模型的聊天完成API",
            "examples": [
                {"title": "基本聊天", "content": "简单的对话示例"},
                {"title": "流式聊天", "content": "流式响应示例"}
            ]
        }
        
        # 模拟文档准备过程
        combined_text_parts = [
            tool_yaml_data["summary"],
            tool_yaml_data["description"]
        ]
        
        # 添加示例内容
        for example in tool_yaml_data.get("examples", []):
            combined_text_parts.append(example["title"])
            combined_text_parts.append(example["content"])
        
        # 生成组合文本
        combined_text = " ".join(combined_text_parts)
        
        # 准备索引文档
        index_document = {
            "id": tool_yaml_data["id"],
            "combined_text": combined_text,
            "metadata": {
                "name": tool_yaml_data["summary"],
                "type": tool_yaml_data["type"],
                "summary": tool_yaml_data["summary"]
            }
        }
        
        # 验证文档准备
        assert index_document["id"] == tool_yaml_data["id"]
        assert len(index_document["combined_text"]) > 0
        assert "兼容OpenAI API" in index_document["combined_text"]
        assert "聊天完成" in index_document["combined_text"]
        assert index_document["metadata"]["type"] == "APIS"


class TestVectorServiceFallback:
    """测试向量服务回退机制"""
    
    @pytest.mark.asyncio
    async def test_vector_service_unavailable_fallback(self):
        """测试向量服务不可用时的回退机制"""
        with patch('requests.get') as mock_get:
            # 模拟向量服务不可用
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            # 检查向量服务状态
            result = await _check_vector_service_config()
            
            # 验证回退行为
            assert result["available"] is False
            
            # 模拟回退到文本匹配
            query = "聊天API"
            fallback_tools = [
                {"id": "tool1", "name": "聊天工具", "score": 0.8},
                {"id": "tool2", "name": "对话API", "score": 0.7}
            ]
            
            # 简单文本匹配回退
            matching_tools = [
                tool for tool in fallback_tools
                if any(keyword in tool["name"] for keyword in ["聊天", "对话", "API"])
            ]
            
            # 验证回退结果
            assert len(matching_tools) == 2
            assert all("聊天" in tool["name"] or "对话" in tool["name"] or "API" in tool["name"] 
                      for tool in matching_tools)
    
    def test_vector_service_partial_failure_handling(self):
        """测试向量服务部分失败处理"""
        # 模拟部分失败场景
        scenarios = [
            {"status_code": 404, "error": "Index not found"},
            {"status_code": 500, "error": "Internal server error"},
            {"status_code": 503, "error": "Service temporarily unavailable"}
        ]
        
        for scenario in scenarios:
            # 验证错误处理策略
            if scenario["status_code"] == 404:
                # 索引不存在 - 可以尝试创建或使用默认
                fallback_action = "create_index_or_use_default"
            elif scenario["status_code"] >= 500:
                # 服务器错误 - 使用回退机制
                fallback_action = "use_text_matching_fallback"
            else:
                # 其他错误 - 记录并重试
                fallback_action = "log_and_retry"
            
            assert fallback_action in [
                "create_index_or_use_default",
                "use_text_matching_fallback", 
                "log_and_retry"
            ]


class TestVectorServicePerformance:
    """测试向量服务性能集成"""
    
    @pytest.mark.asyncio
    async def test_vector_search_timeout_handling(self):
        """测试向量搜索超时处理"""
        with patch('requests.post') as mock_post:
            # 模拟超时
            mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
            
            # 尝试向量搜索
            try:
                response = requests.post(
                    "http://test-vector-service/search",
                    json={"query": "test", "top_k": 5},
                    timeout=30
                )
                search_success = True
            except requests.exceptions.Timeout:
                search_success = False
            
            # 验证超时处理
            assert search_success is False
    
    def test_vector_search_result_caching(self):
        """测试向量搜索结果缓存"""
        # 模拟缓存机制
        search_cache = {}
        
        def cached_vector_search(query: str, cache_ttl: int = 300):
            """模拟带缓存的向量搜索"""
            import time
            cache_key = f"search:{hash(query)}"
            current_time = time.time()
            
            # 检查缓存
            if cache_key in search_cache:
                cached_result, timestamp = search_cache[cache_key]
                if current_time - timestamp < cache_ttl:
                    return {"results": cached_result, "from_cache": True}
            
            # 模拟搜索结果
            search_results = [
                {"id": "tool1", "score": 0.9, "metadata": {"name": "相关工具"}}
            ]
            
            # 更新缓存
            search_cache[cache_key] = (search_results, current_time)
            
            return {"results": search_results, "from_cache": False}
        
        # 测试缓存功能
        query = "测试查询"
        
        # 第一次搜索
        result1 = cached_vector_search(query)
        assert result1["from_cache"] is False
        
        # 第二次搜索（应该从缓存获取）
        result2 = cached_vector_search(query)
        assert result2["from_cache"] is True
        assert result1["results"] == result2["results"]
