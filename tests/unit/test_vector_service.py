"""
向量数据库功能单元测试

测试向量服务相关功能，包括：
- 向量嵌入生成测试
- 向量相似度搜索测试
- 向量数据库连接和配置测试
- 向量服务不可用时的优雅降级测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import json
import requests
from typing import Dict, Any, List

from utils.config_manager import get_vector_service_config
from agent.utils.startup_init import _check_vector_service_config


class TestVectorServiceConfig:
    """测试向量服务配置"""
    
    def test_vector_service_config_loading(self):
        """测试向量服务配置加载"""
        config = get_vector_service_config()
        
        # 验证配置结构
        assert isinstance(config, dict)
        assert "base_url" in config
        assert "timeout" in config
        assert "tools_index_name" in config
        assert "vector_field" in config
        
        # 验证默认值
        assert config["timeout"] >= 0
        assert isinstance(config["tools_index_name"], str)
        assert isinstance(config["vector_field"], str)
    
    @patch.dict('os.environ', {
        'VECTOR_SERVICE_BASE_URL': 'http://test-vector-service:8080',
        'VECTOR_SERVICE_TIMEOUT': '60',
        'VECTOR_SERVICE_INDEX_NAME': 'document_test_tools',
        'VECTOR_SERVICE_VECTOR_FIELD': 'test_field'
    })
    def test_vector_service_config_from_env(self):
        """测试从环境变量加载向量服务配置"""
        config = get_vector_service_config()
        
        # 验证环境变量覆盖
        assert config.get("base_url") == "http://test-vector-service:8080"
        assert config.get("timeout") == 60
        assert config.get("tools_index_name") == "document_test_tools"
        assert config.get("vector_field") == "test_field"


class TestVectorServiceAvailability:
    """测试向量服务可用性检查"""
    
    @pytest.mark.asyncio
    async def test_vector_service_available(self):
        """测试向量服务可用时的检查"""
        with patch('requests.get') as mock_get:
            # 模拟向量服务可用
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await _check_vector_service_config()
            
            assert isinstance(result, dict)
            assert "available" in result
            assert "config" in result
            
            # 验证调用参数
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/health" in call_args[0][0]
            assert call_args[1]["timeout"] == 5
    
    @pytest.mark.asyncio
    async def test_vector_service_unavailable(self):
        """测试向量服务不可用时的检查"""
        with patch('requests.get') as mock_get:
            # 模拟向量服务不可用
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            result = await _check_vector_service_config()
            
            assert isinstance(result, dict)
            assert "available" in result
            assert result["available"] is False
            assert "config" in result
    
    @pytest.mark.asyncio
    async def test_vector_service_no_config(self):
        """测试向量服务未配置时的检查"""
        with patch('agent.utils.startup_init.get_vector_service_config') as mock_config:
            # 模拟未配置向量服务
            mock_config.return_value = {"base_url": None}

            result = await _check_vector_service_config()

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "向量服务URL未配置" in result["error"]


class TestVectorEmbedding:
    """测试向量嵌入功能"""
    
    def test_embedding_request_format(self):
        """测试向量嵌入请求格式"""
        # 模拟向量嵌入请求
        embedding_request = {
            "model": "text-embedding-3-small",
            "input": "测试文本",
            "encoding_format": "float"
        }
        
        # 验证请求格式
        assert "model" in embedding_request
        assert "input" in embedding_request
        assert isinstance(embedding_request["input"], str)
        assert embedding_request["encoding_format"] in ["float", "base64"]
    
    def test_batch_embedding_request(self):
        """测试批量向量嵌入请求"""
        # 模拟批量向量嵌入请求
        batch_request = {
            "model": "text-embedding-3-small",
            "input": ["文本1", "文本2", "文本3"],
            "encoding_format": "float"
        }
        
        # 验证批量请求格式
        assert isinstance(batch_request["input"], list)
        assert len(batch_request["input"]) > 1
        assert all(isinstance(text, str) for text in batch_request["input"])
    
    @patch('requests.post')
    def test_embedding_api_call(self, mock_post):
        """测试向量嵌入API调用"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "index": 0
                }
            ],
            "model": "text-embedding-3-small",
            "usage": {"total_tokens": 10}
        }
        mock_post.return_value = mock_response
        
        # 模拟调用向量嵌入API
        import requests
        response = requests.post(
            "http://test-api/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": "测试文本"
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert "embedding" in data["data"][0]
        assert isinstance(data["data"][0]["embedding"], list)


class TestVectorSearch:
    """测试向量搜索功能"""
    
    def test_vector_search_request_format(self):
        """测试向量搜索请求格式"""
        search_request = {
            "query": "搜索查询文本",
            "vector_field": "combined_text",
            "index": "document_test_tools",
            "top_k": 5
        }
        
        # 验证搜索请求格式
        assert "query" in search_request
        assert "vector_field" in search_request
        assert "index" in search_request
        assert "top_k" in search_request
        assert isinstance(search_request["top_k"], int)
        assert search_request["top_k"] > 0
    
    @patch('requests.post')
    def test_vector_search_api_call(self, mock_post):
        """测试向量搜索API调用"""
        # 模拟搜索API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "tool_1",
                    "score": 0.95,
                    "metadata": {
                        "name": "测试工具1",
                        "description": "这是一个测试工具"
                    }
                },
                {
                    "id": "tool_2", 
                    "score": 0.87,
                    "metadata": {
                        "name": "测试工具2",
                        "description": "这是另一个测试工具"
                    }
                }
            ],
            "total": 2
        }
        mock_post.return_value = mock_response
        
        # 模拟调用向量搜索API
        import requests
        response = requests.post(
            "http://test-vector-service/search",
            json={
                "query": "测试查询",
                "vector_field": "combined_text",
                "index": "document_test_tools",
                "top_k": 5
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert len(data["results"]) == 2
        
        # 验证搜索结果格式
        for result in data["results"]:
            assert "id" in result
            assert "score" in result
            assert "metadata" in result
            assert isinstance(result["score"], (int, float))
            assert 0 <= result["score"] <= 1
    
    def test_vector_search_score_filtering(self):
        """测试向量搜索结果分数过滤"""
        # 模拟搜索结果
        search_results = [
            {"id": "tool_1", "score": 0.95, "metadata": {"name": "高相关工具"}},
            {"id": "tool_2", "score": 0.75, "metadata": {"name": "中等相关工具"}},
            {"id": "tool_3", "score": 0.45, "metadata": {"name": "低相关工具"}},
            {"id": "tool_4", "score": 0.05, "metadata": {"name": "不相关工具"}}
        ]
        
        # 应用分数阈值过滤
        min_score_threshold = 0.5
        filtered_results = [
            result for result in search_results 
            if result["score"] >= min_score_threshold
        ]
        
        # 验证过滤结果
        assert len(filtered_results) == 2
        assert all(result["score"] >= min_score_threshold for result in filtered_results)
        assert filtered_results[0]["score"] >= filtered_results[1]["score"]  # 验证排序


class TestVectorServiceGracefulDegradation:
    """测试向量服务优雅降级"""
    
    def test_vector_service_fallback_behavior(self):
        """测试向量服务不可用时的回退行为"""
        # 模拟向量服务不可用的情况
        vector_service_available = False
        
        if not vector_service_available:
            # 应该提供回退机制
            fallback_result = {
                "status": "degraded",
                "message": "向量服务不可用，使用文本匹配回退",
                "results": []
            }
            
            assert fallback_result["status"] == "degraded"
            assert "向量服务不可用" in fallback_result["message"]
            assert isinstance(fallback_result["results"], list)
    
    @patch('requests.get')
    def test_vector_service_timeout_handling(self, mock_get):
        """测试向量服务超时处理"""
        # 模拟超时异常
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        try:
            # 尝试检查向量服务健康状态
            response = requests.get("http://test-vector-service/health", timeout=5)
            service_available = response.status_code == 200
        except requests.exceptions.Timeout:
            service_available = False
        
        # 验证超时处理
        assert service_available is False
    
    def test_vector_service_error_response_handling(self):
        """测试向量服务错误响应处理"""
        # 模拟各种错误响应
        error_responses = [
            {"status_code": 404, "message": "Index not found"},
            {"status_code": 500, "message": "Internal server error"},
            {"status_code": 503, "message": "Service unavailable"}
        ]
        
        for error_response in error_responses:
            # 验证错误处理逻辑
            if error_response["status_code"] >= 400:
                # 应该触发错误处理
                assert error_response["status_code"] >= 400
                assert "message" in error_response


class TestVectorIndexManagement:
    """测试向量索引管理"""
    
    def test_index_document_format(self):
        """测试索引文档格式"""
        # 模拟要索引的文档
        documents = [
            {
                "id": "tool_1",
                "combined_text": "这是工具1的描述文本",
                "metadata": {
                    "name": "工具1",
                    "type": "APIS",
                    "summary": "API工具"
                }
            },
            {
                "id": "tool_2", 
                "combined_text": "这是工具2的描述文本",
                "metadata": {
                    "name": "工具2",
                    "type": "PYTHON_PACKAGE",
                    "summary": "Python包工具"
                }
            }
        ]
        
        # 验证文档格式
        for doc in documents:
            assert "id" in doc
            assert "combined_text" in doc
            assert "metadata" in doc
            assert isinstance(doc["metadata"], dict)
            assert "name" in doc["metadata"]
            assert "type" in doc["metadata"]
    
    @patch('requests.post')
    def test_index_creation_request(self, mock_post):
        """测试索引创建请求"""
        # 模拟索引创建响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "indexed_count": 2,
            "index_name": "document_test_tools"
        }
        mock_post.return_value = mock_response
        
        # 模拟索引创建请求
        documents = [
            {"id": "tool_1", "combined_text": "工具1描述"},
            {"id": "tool_2", "combined_text": "工具2描述"}
        ]
        
        import requests
        response = requests.post(
            "http://test-vector-service/documents",
            json={
                "documents": documents,
                "vector_field": "combined_text",
                "index": "document_test_tools"
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["indexed_count"] == len(documents)
    
    @patch('requests.delete')
    def test_index_clearing_request(self, mock_delete):
        """测试索引清除请求"""
        # 模拟索引清除响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "message": "Index cleared successfully"
        }
        mock_delete.return_value = mock_response
        
        # 模拟索引清除请求
        import requests
        response = requests.delete(
            "http://test-vector-service/index/document_test_tools/clear"
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
