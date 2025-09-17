"""
文档索引器 - 会话级索引管理

基于canvas.md设计文档实现的索引管理器，支持：
1. 会话级命名空间管理
2. 调用向量数据库API
3. 支持增量更新
4. 索引清理和维护
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from utils.config_manager import multilingual_config, get_vector_service_config
from .document_processor import DocumentChunk
from utils.vector_service_client import get_vector_service_client

logger = logging.getLogger(__name__)


@dataclass
class IndexResult:
    """索引结果数据结构"""
    success: bool
    index_name: str
    indexed_count: int
    total_chunks: int
    processing_time: float
    error_message: Optional[str] = None


class DocumentIndexer:
    """文档索引器 - 实现会话级索引管理"""
    
    def __init__(self,
                 vector_service_url: Optional[str] = None,
                 timeout: int = 30,
                 vector_field: str = "content"):
        """
        初始化文档索引器

        Args:
            vector_service_url: 向量服务URL（保留用于兼容性）
            timeout: 请求超时时间（保留用于兼容性）
            vector_field: 向量字段名
        """
        self.config = multilingual_config

        # 获取向量服务客户端
        self.vector_client = get_vector_service_client()

        # 保留配置参数用于兼容性
        vector_config = self.config.get_vector_service_config()
        self.vector_service_url = (
            vector_service_url or
            vector_config.get("base_url", "http://localhost:8080")
        )
        self.timeout = timeout
        self.vector_field = vector_field

        logger.info(f"文档索引器初始化完成，向量服务: {self.vector_service_url}, 向量字段: {self.vector_field}")
    
    async def index_documents(self,
                            session_id: str,
                            chunks: List[DocumentChunk],
                            embeddings: Optional[List[Dict[str, Any]]] = None) -> IndexResult:
        """
        索引文档到会话专属命名空间

        Args:
            session_id: 会话ID
            chunks: 文档块列表
            embeddings: 可选的嵌入结果列表（已弃用，向量服务会自动处理向量化）

        Returns:
            索引结果
        """
        start_time = time.time()
        index_name = self._get_session_index_name(session_id)
        
        logger.info(f"开始索引文档到会话 {session_id}，索引名: {index_name}")
        
        try:
            # 检查索引是否存在
            index_exists = await self._check_index_exists(index_name)

            if index_exists:
                # 如果索引存在，清空它
                logger.info(f"索引 {index_name} 已存在，正在清空...")
                print(f"🧹 索引 {index_name} 已存在，正在清空...")  # 调试输出
                clear_success = await self._clear_session_index(index_name)
                if not clear_success:
                    logger.error(f"清空索引 {index_name} 失败")
                    print(f"❌ 清空索引 {index_name} 失败")  # 调试输出
                else:
                    print(f"✅ 清空索引 {index_name} 成功")  # 调试输出
            else:
                # 如果索引不存在，让向量服务自动创建
                logger.info(f"索引 {index_name} 不存在，将由向量服务自动创建...")
                print(f"🔧 索引 {index_name} 不存在，将由向量服务自动创建...")  # 调试输出

            # 2. 准备文档数据
            documents = self._prepare_documents(chunks, embeddings)

            if not documents:
                logger.warning("没有有效的文档需要索引")
                return IndexResult(
                    success=False,
                    index_name=index_name,
                    indexed_count=0,
                    total_chunks=len(chunks),
                    processing_time=time.time() - start_time,
                    error_message="没有有效的文档需要索引"
                )

            # 3. 调用向量服务进行索引
            result = await self._call_index_api(index_name, documents)
            
            processing_time = time.time() - start_time
            
            if result.get("success", False):
                indexed_count = result.get("count", 0)
                logger.info(f"文档索引成功，索引 {indexed_count} 个文档，耗时 {processing_time:.2f} 秒")
                
                return IndexResult(
                    success=True,
                    index_name=index_name,
                    indexed_count=indexed_count,
                    total_chunks=len(chunks),
                    processing_time=processing_time
                )
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"文档索引失败: {error_msg}")
                
                return IndexResult(
                    success=False,
                    index_name=index_name,
                    indexed_count=0,
                    total_chunks=len(chunks),
                    processing_time=processing_time,
                    error_message=error_msg
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"文档索引异常: {str(e)}")
            
            return IndexResult(
                success=False,
                index_name=index_name,
                indexed_count=0,
                total_chunks=len(chunks),
                processing_time=processing_time,
                error_message=str(e)
            )

    async def search_documents(self, 
                             session_id: str,
                             query: str,
                             top_k: int = 5) -> Dict[str, Any]:
        """
        在会话索引中搜索文档
        
        Args:
            session_id: 会话ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        index_name = self._get_session_index_name(session_id)
        
        try:
            # 使用向量服务客户端进行搜索
            result = await self.vector_client.search_documents(
                query=query,
                vector_field=self.vector_field,
                index=index_name,
                top_k=top_k
            )

            if "error" not in result:
                logger.info(f"搜索成功，返回 {result.get('total', 0)} 个结果")
                return result
            else:
                error_msg = result.get("error", "未知搜索错误")
                logger.error(f"搜索失败: {error_msg}")
                return {"error": error_msg, "results": [], "total": 0}

        except Exception as e:
            error_msg = f"搜索请求失败: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "results": [], "total": 0}
    
    async def clear_session_index(self, session_id: str) -> bool:
        """
        清空会话索引
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        index_name = self._get_session_index_name(session_id)
        return await self._clear_session_index(index_name)
    
    def _get_session_index_name(self, session_id: str) -> str:
        """
        生成会话专属的索引名称

        Args:
            session_id: 会话ID

        Returns:
            索引名称
        """
        # 向量服务要求索引名称必须以 'document_' 开头
        # 同时保持会话级隔离：document_session_{sessionId}
        return f"document_session_{session_id}"
    
    def _prepare_documents(self,
                          chunks: List[DocumentChunk],
                          embeddings: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        准备文档数据用于索引

        Args:
            chunks: 文档块列表
            embeddings: 可选的嵌入结果列表（已弃用，向量服务会自动处理向量化）

        Returns:
            准备好的文档列表
        """
        documents = []

        for chunk in chunks:
            # 构建文档对象 - 按照向量服务API规范
            # 向量服务会自动为vector_field指定的字段生成嵌入向量
            document = {
                "id": chunk.chunk_id,
                "metadata": chunk.metadata,
                # 向量字段 - 向量服务会为这个字段生成嵌入向量
                self.vector_field: chunk.content
            }

            documents.append(document)

        logger.info(f"准备了 {len(documents)} 个文档用于索引")
        # 调试：打印第一个文档的格式
        if documents:
            print(f"🔍 第一个文档格式: {documents[0]}")
            logger.info(f"第一个文档格式: {documents[0]}")
        return documents
    
    async def _call_index_api(self,
                            index_name: str,
                            documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        调用向量服务索引API

        Args:
            index_name: 索引名称
            documents: 文档列表

        Returns:
            API响应结果
        """
        try:
            print(f"🚀 发送请求到向量服务: 索引={index_name}, 文档数量={len(documents)}")  # 调试输出
            logger.info(f"开始索引 {len(documents)} 个文档到索引 {index_name}...")

            # 使用向量服务客户端
            result = await self.vector_client.create_documents(
                documents=documents,
                vector_field=self.vector_field,
                index=index_name
            )

            if result.get("success"):
                indexed_count = result.get("count", 0)
                actual_index = result.get("index", index_name)
                logger.info(f"成功索引 {indexed_count} 个文档到索引 {actual_index}")
                return {"success": True, "count": indexed_count, "index": actual_index}
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"索引失败: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"索引API调用异常: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def _check_index_exists(self, index_name: str) -> bool:
        """
        检查索引是否存在

        Args:
            index_name: 索引名称

        Returns:
            索引是否存在
        """
        try:
            # 使用向量服务客户端
            result = await self.vector_client.check_index_exists(index_name)
            exists = result.get("exists", False)

            if exists:
                doc_count = result.get("document_count", 0)
                logger.info(f"索引 {index_name} 存在，包含 {doc_count} 个文档")
            else:
                logger.info(f"索引 {index_name} 不存在")

            return exists

        except Exception as e:
            logger.warning(f"检查索引存在性异常: {str(e)}")
            return False

    async def _create_index(self, index_name: str) -> bool:
        """
        创建索引

        Args:
            index_name: 索引名称

        Returns:
            是否成功创建
        """
        try:
            # 使用向量服务客户端
            result = await self.vector_client.create_index(
                index_name=index_name,
                vector_field=self.vector_field,
                vector_dimension=1024  # 默认维度，向量服务会自动调整
            )

            if result.get("success"):
                created = result.get("created", False)
                if created:
                    logger.info(f"成功创建索引 {index_name}")
                else:
                    logger.info(f"索引 {index_name} 已存在")
                return True
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"创建索引失败: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"创建索引异常: {str(e)}")
            return False

    async def _clear_session_index(self, index_name: str) -> bool:
        """
        清空会话索引

        Args:
            index_name: 索引名称

        Returns:
            是否成功
        """
        try:
            # 使用向量服务客户端
            result = await self.vector_client.clear_index(index_name)

            if result.get("success"):
                deleted_count = result.get("deleted_count", 0)
                logger.info(f"清空索引 {index_name} 成功，删除 {deleted_count} 个文档")
                return True
            else:
                error_msg = result.get("error", "未知错误")
                logger.warning(f"清空索引失败: {error_msg}")
                return False

        except Exception as e:
            logger.warning(f"清空索引异常: {str(e)}")
            return False
