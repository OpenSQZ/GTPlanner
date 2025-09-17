"""
向量服务客户端 - 基于OpenAPI规范的统一客户端

基于openapi.json规范实现的向量服务客户端，提供：
1. 文档创建和向量化
2. 向量搜索
3. 索引管理
4. 健康检查

完全替代OpenAI客户端，所有向量化操作都通过向量服务完成。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import time
import httpx
import requests
from dataclasses import dataclass

from utils.config_manager import get_vector_service_config

logger = logging.getLogger(__name__)


@dataclass
class VectorServiceConfig:
    """向量服务配置"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class VectorServiceClient:
    """向量服务客户端 - 基于OpenAPI规范"""
    
    def __init__(self, config: Optional[VectorServiceConfig] = None):
        """
        初始化向量服务客户端
        
        Args:
            config: 向量服务配置，如果为None则从配置文件读取
        """
        if config is None:
            vector_config = get_vector_service_config()
            self.config = VectorServiceConfig(
                base_url=vector_config.get("base_url"),
                timeout=vector_config.get("timeout", 30),
                max_retries=3,
                retry_delay=1.0
            )
        else:
            self.config = config
            
        if not self.config.base_url:
            raise ValueError("向量服务URL未配置，请设置VECTOR_SERVICE_BASE_URL环境变量")
            
        logger.info(f"向量服务客户端初始化完成，服务地址: {self.config.base_url}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/health",
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    return {"healthy": True, "data": response.json()}
                else:
                    return {"healthy": False, "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    async def create_documents(self, 
                             documents: List[Dict[str, Any]], 
                             vector_field: str,
                             index: Optional[str] = None) -> Dict[str, Any]:
        """
        创建文档并进行向量化
        
        Args:
            documents: 文档列表
            vector_field: 需要向量化的字段名
            index: 可选的索引名
            
        Returns:
            创建结果
        """
        request_data = {
            "documents": documents,
            "vector_field": vector_field
        }
        
        if index:
            request_data["index"] = index
            
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.config.base_url}/documents",
                        json=request_data,
                        timeout=self.config.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"成功创建 {result.get('count', 0)} 个文档到索引 {result.get('index', 'unknown')}")
                        return {"success": True, **result}
                    else:
                        error_msg = f"创建文档失败: {response.status_code}, {response.text}"
                        logger.warning(error_msg)
                        if attempt == self.config.max_retries - 1:
                            return {"success": False, "error": error_msg}
                        
            except Exception as e:
                error_msg = f"创建文档异常 (尝试 {attempt + 1}/{self.config.max_retries}): {str(e)}"
                logger.warning(error_msg)
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    return {"success": False, "error": str(e)}
    
    async def search_documents(self,
                             query: str,
                             vector_field: str,
                             index: str,
                             top_k: int = 5) -> Dict[str, Any]:
        """
        搜索文档（带重试）

        Args:
            query: 查询文本
            vector_field: 向量字段名
            index: 目标索引名
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        request_data = {
            "query": query,
            "vector_field": vector_field,
            "index": index,
            "top_k": top_k
        }

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.config.base_url}/search",
                        json=request_data,
                        timeout=self.config.timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        logger.debug(f"搜索成功，返回 {result.get('total', 0)} 个结果")
                        return result
                    else:
                        last_error = f"搜索失败: {response.status_code}, {response.text}"
                        logger.warning(f"{last_error} (attempt {attempt+1}/{self.config.max_retries})")
                        # 502/503/504 等暂时性错误重试
                        if response.status_code in (502, 503, 504) and attempt < self.config.max_retries - 1:
                            await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                            continue
                        return {"error": last_error, "results": [], "total": 0}

            except Exception as e:
                last_error = f"搜索异常 (attempt {attempt+1}/{self.config.max_retries}): {str(e)}"
                logger.warning(last_error)
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                return {"error": str(e), "results": [], "total": 0}

        # 理论上不会到这
        return {"error": last_error or "unknown error", "results": [], "total": 0}
    
    async def create_index(self,
                          index_name: str,
                          vector_field: str = "content",
                          vector_dimension: int = 1024,
                          description: Optional[str] = None) -> Dict[str, Any]:
        """
        创建索引
        
        Args:
            index_name: 索引名称
            vector_field: 向量字段名
            vector_dimension: 向量维度
            description: 索引描述
            
        Returns:
            创建结果
        """
        request_data = {
            "vector_field": vector_field,
            "vector_dimension": vector_dimension
        }
        
        if description:
            request_data["description"] = description
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.config.base_url}/index/{index_name}",
                    json=request_data,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"索引操作完成: {index_name}, 是否新创建: {result.get('created', False)}")
                    return {"success": True, **result}
                else:
                    error_msg = f"创建索引失败: {response.status_code}, {response.text}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            error_msg = f"创建索引异常: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def check_index_exists(self, index_name: str) -> Dict[str, Any]:
        """
        检查索引是否存在
        
        Args:
            index_name: 索引名称
            
        Returns:
            存在性检查结果
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/index/{index_name}/exists",
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    exists = result.get("exists", False)
                    if exists:
                        doc_count = result.get("document_count", 0)
                        logger.debug(f"索引 {index_name} 存在，包含 {doc_count} 个文档")
                    else:
                        logger.debug(f"索引 {index_name} 不存在")
                    return result
                else:
                    logger.warning(f"检查索引存在性失败: {response.status_code}, {response.text}")
                    return {"exists": False, "index": index_name, "error": response.text}
                    
        except Exception as e:
            logger.warning(f"检查索引存在性异常: {str(e)}")
            return {"exists": False, "index": index_name, "error": str(e)}
    
    async def clear_index(self, index_name: str) -> Dict[str, Any]:
        """
        清空索引
        
        Args:
            index_name: 索引名称
            
        Returns:
            清空结果
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.config.base_url}/index/{index_name}/clear",
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = result.get("deleted_count", 0)
                    logger.info(f"成功清空索引 {index_name}，删除 {deleted_count} 个文档")
                    return {"success": True, **result}
                else:
                    error_msg = f"清空索引失败: {response.status_code}, {response.text}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            error_msg = f"清空索引异常: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def list_indices(self) -> Dict[str, Any]:
        """
        获取索引列表
        
        Returns:
            索引列表
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/indices",
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    indices = result.get("indices", [])
                    logger.debug(f"获取到 {len(indices)} 个索引")
                    return result
                else:
                    error_msg = f"获取索引列表失败: {response.status_code}, {response.text}"
                    logger.error(error_msg)
                    return {"indices": [], "error": error_msg}
                    
        except Exception as e:
            error_msg = f"获取索引列表异常: {str(e)}"
            logger.error(error_msg)
            return {"indices": [], "error": error_msg}
    
    def sync_search_documents(self,
                            query: str,
                            vector_field: str,
                            index: str,
                            top_k: int = 5) -> Dict[str, Any]:
        """
        同步搜索文档（用于兼容现有的同步代码）
        
        Args:
            query: 查询文本
            vector_field: 向量字段名
            index: 目标索引名
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        request_data = {
            "query": query,
            "vector_field": vector_field,
            "index": index,
            "top_k": top_k
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/search",
                json=request_data,
                timeout=self.config.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"同步搜索成功，返回 {result.get('total', 0)} 个结果")
                return result
            else:
                error_msg = f"同步搜索失败: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return {"error": error_msg, "results": [], "total": 0}
                
        except Exception as e:
            error_msg = f"同步搜索异常: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "results": [], "total": 0}


# 全局客户端实例
_vector_client: Optional[VectorServiceClient] = None


def get_vector_service_client() -> VectorServiceClient:
    """
    获取向量服务客户端实例（单例模式）
    
    Returns:
        向量服务客户端实例
    """
    global _vector_client
    if _vector_client is None:
        _vector_client = VectorServiceClient()
    return _vector_client
