"""
文档嵌入模块 - 统一接口

基于canvas.md设计文档实现的文档嵌入系统，提供：
1. 统一的文档索引接口
2. 会话级文档知识感知
3. 智能文档分割和向量化
4. 检索增强生成(RAG)支持

主要组件：
- DocumentProcessor: 智能文档分割
- VectorServiceClient: 向量服务客户端
- DocumentIndexer: 索引管理
- DocumentEmbeddingPipeline: 完整的处理流水线
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from .document_processor import DocumentProcessor, DocumentChunk
from utils.vector_service_client import get_vector_service_client
from .document_indexer import DocumentIndexer, IndexResult

logger = logging.getLogger(__name__)


@dataclass
class IndexDocumentsRequest:
    """索引文档请求"""
    session_id: str
    documents: List[Dict[str, str]]  # [{"documentId": "1.md", "content": "..."}]


@dataclass
class IndexDocumentsResponse:
    """索引文档响应"""
    status: str
    message: str
    indexed_documents: int
    total_chunks_created: int
    processing_time: float
    session_index_name: str
    error_details: Optional[str] = None


@dataclass
class SearchDocumentsRequest:
    """搜索文档请求"""
    session_id: str
    query: str
    top_k: int = 5


@dataclass
class UpdateKnowledgeBaseRequest:
    """更新知识库请求"""
    session_id: str
    updated_documents: List[Dict[str, str]]


class DocumentEmbeddingPipeline:
    """文档嵌入流水线 - 完整的处理流程"""

    def __init__(self,
                 embedding_model: str = "text-embedding-3-small",
                 chunk_size: int = 1000,
                 min_chunk_size: int = 100,
                 chunk_overlap: int = 200,
                 batch_size: int = 100,
                 vector_service_url: Optional[str] = None,
                 vector_field: str = "content"):
        """
        初始化文档嵌入流水线

        Args:
            embedding_model: 嵌入模型名称（保留用于兼容性，实际由向量服务处理）
            chunk_size: 目标块大小
            min_chunk_size: 最小块大小
            chunk_overlap: 块重叠大小
            batch_size: 批处理大小（保留用于兼容性）
            vector_service_url: 向量服务URL
            vector_field: 向量字段名
        """
        # 初始化各个组件
        self.processor = DocumentProcessor(
            chunk_size=chunk_size,
            min_chunk_size=min_chunk_size,
            chunk_overlap=chunk_overlap
        )

        # 获取向量服务客户端
        self.vector_client = get_vector_service_client()

        self.indexer = DocumentIndexer(
            vector_service_url=vector_service_url,
            vector_field=vector_field
        )

        # 保存配置参数
        self.embedding_model = embedding_model
        self.batch_size = batch_size
        self.vector_field = vector_field

        logger.info(f"文档嵌入流水线初始化完成，向量字段: {vector_field}")
    
    async def index_documents(self, request: IndexDocumentsRequest) -> IndexDocumentsResponse:
        """
        完整的文档索引流程
        
        Args:
            request: 索引请求
            
        Returns:
            索引响应
        """
        start_time = time.time()
        session_id = request.session_id
        documents = request.documents
        
        logger.info(f"开始处理会话 {session_id} 的文档索引，包含 {len(documents)} 个文档")
        
        try:
            # 步骤1: 文档分割
            logger.info("步骤1: 智能文档分割")
            chunks = self.processor.process_documents(session_id, documents)
            
            if not chunks:
                return IndexDocumentsResponse(
                    status="error",
                    message="文档分割失败，没有生成有效的文档块",
                    indexed_documents=0,
                    total_chunks_created=0,
                    processing_time=time.time() - start_time,
                    session_index_name=f"session-{session_id}",
                    error_details="文档分割阶段失败"
                )
            
            logger.info(f"文档分割完成，生成 {len(chunks)} 个文档块")
            
            # 步骤2: 直接索引存储（让向量服务处理向量化）
            logger.info("步骤2: 会话级索引存储（向量服务将自动处理向量化）")
            index_result = await self.indexer.index_documents(session_id, chunks, [])
            
            processing_time = time.time() - start_time
            
            if index_result.success:
                logger.info(f"文档索引完成，总耗时 {processing_time:.2f} 秒")
                
                return IndexDocumentsResponse(
                    status="success",
                    message="索引任务完成。",
                    indexed_documents=len(documents),
                    total_chunks_created=len(chunks),
                    processing_time=processing_time,
                    session_index_name=index_result.index_name
                )
            else:
                return IndexDocumentsResponse(
                    status="error",
                    message="文档索引失败",
                    indexed_documents=0,
                    total_chunks_created=len(chunks),
                    processing_time=processing_time,
                    session_index_name=index_result.index_name,
                    error_details=index_result.error_message
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"文档索引流程异常: {str(e)}")
            
            return IndexDocumentsResponse(
                status="error",
                message=f"索引流程异常: {str(e)}",
                indexed_documents=0,
                total_chunks_created=0,
                processing_time=processing_time,
                session_index_name=f"session-{session_id}",
                error_details=str(e)
            )
    
    async def search_documents(self, request: SearchDocumentsRequest) -> Dict[str, Any]:
        """
        在会话文档中搜索
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索结果
        """
        logger.info(f"在会话 {request.session_id} 中搜索: {request.query}")
        
        try:
            # 调用索引器搜索
            result = await self.indexer.search_documents(
                session_id=request.session_id,
                query=request.query,
                top_k=request.top_k
            )
            
            return result
            
        except Exception as e:
            logger.error(f"文档搜索异常: {str(e)}")
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "took": 0
            }
    
    async def update_knowledge_base(self, request: UpdateKnowledgeBaseRequest) -> IndexDocumentsResponse:
        """
        更新知识库（增量更新）
        
        Args:
            request: 更新请求
            
        Returns:
            更新响应
        """
        logger.info(f"更新会话 {request.session_id} 的知识库")
        
        # 对于简化实现，直接重新索引
        index_request = IndexDocumentsRequest(
            session_id=request.session_id,
            documents=request.updated_documents
        )
        
        return await self.index_documents(index_request)
    
    async def clear_session_index(self, session_id: str) -> bool:
        """
        清空会话索引
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        logger.info(f"清空会话 {session_id} 的索引")
        return await self.indexer.clear_session_index(session_id)
    
    def get_processing_stats(self, total_chunks: int, processing_time: float) -> Dict[str, Any]:
        """
        获取处理统计信息

        Args:
            total_chunks: 总文档块数
            processing_time: 处理时间

        Returns:
            统计信息
        """
        return {
            "total_chunks": total_chunks,
            "processing_time": processing_time,
            "average_time_per_chunk": processing_time / total_chunks if total_chunks > 0 else 0,
            "embedding_model": self.embedding_model,
            "vector_field": self.vector_field
        }


# 全局流水线实例
_pipeline_instance = None


def get_document_embedding_pipeline(**kwargs) -> DocumentEmbeddingPipeline:
    """
    获取全局文档嵌入流水线实例
    
    Args:
        **kwargs: 初始化参数
        
    Returns:
        流水线实例
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DocumentEmbeddingPipeline(**kwargs)
    return _pipeline_instance


# 便捷函数
async def index_documents(session_id: str, 
                         documents: List[Dict[str, str]]) -> IndexDocumentsResponse:
    """
    便捷的文档索引函数
    
    Args:
        session_id: 会话ID
        documents: 文档列表
        
    Returns:
        索引响应
    """
    pipeline = get_document_embedding_pipeline()
    request = IndexDocumentsRequest(session_id=session_id, documents=documents)
    return await pipeline.index_documents(request)


async def search_documents(session_id: str, 
                          query: str, 
                          top_k: int = 5) -> Dict[str, Any]:
    """
    便捷的文档搜索函数
    
    Args:
        session_id: 会话ID
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        搜索结果
    """
    pipeline = get_document_embedding_pipeline()
    request = SearchDocumentsRequest(session_id=session_id, query=query, top_k=top_k)
    return await pipeline.search_documents(request)


async def update_knowledge_base(session_id: str, 
                               updated_documents: List[Dict[str, str]]) -> IndexDocumentsResponse:
    """
    便捷的知识库更新函数
    
    Args:
        session_id: 会话ID
        updated_documents: 更新的文档列表
        
    Returns:
        更新响应
    """
    pipeline = get_document_embedding_pipeline()
    request = UpdateKnowledgeBaseRequest(session_id=session_id, updated_documents=updated_documents)
    return await pipeline.update_knowledge_base(request)


# 导出主要类和函数
__all__ = [
    'DocumentProcessor',
    'DocumentIndexer',
    'DocumentEmbeddingPipeline',
    'DocumentChunk',
    'IndexResult',
    'IndexDocumentsRequest',
    'IndexDocumentsResponse',
    'SearchDocumentsRequest',
    'UpdateKnowledgeBaseRequest',
    'get_document_embedding_pipeline',
    'index_documents',
    'search_documents',
    'update_knowledge_base'
]
