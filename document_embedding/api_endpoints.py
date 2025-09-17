"""
文档嵌入API接口

基于canvas.md设计文档实现的API接口，提供：
1. POST /index-documents - 文档首次索引
2. POST /propose-changes - 变更提案（未来实现）
3. POST /update-knowledge-base - 知识库更新
4. POST /search - 文档检索
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from . import (
    get_document_embedding_pipeline,
    IndexDocumentsRequest,
    IndexDocumentsResponse,
    SearchDocumentsRequest,
    UpdateKnowledgeBaseRequest
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/document-embedding", tags=["文档嵌入"])


# 请求模型
class DocumentInput(BaseModel):
    """文档输入模型"""
    documentId: str = Field(..., description="文档的唯一标识符")
    content: str = Field(..., description="文档的完整原始内容")


class IndexDocumentsRequestModel(BaseModel):
    """索引文档请求模型"""
    sessionId: str = Field(..., description="会话的唯一标识符")
    documents: List[DocumentInput] = Field(..., description="文档列表")


class SearchRequestModel(BaseModel):
    """搜索请求模型"""
    sessionId: str = Field(..., description="会话ID")
    query: str = Field(..., description="查询文本")
    topK: int = Field(5, description="返回的结果数量", ge=1, le=20)


class UpdateKnowledgeBaseRequestModel(BaseModel):
    """更新知识库请求模型"""
    sessionId: str = Field(..., description="会话ID")
    updatedDocuments: List[DocumentInput] = Field(..., description="更新的文档列表")


# 响应模型
class IndexDocumentsResponseModel(BaseModel):
    """索引文档响应模型"""
    status: str = Field(..., description="处理状态")
    message: str = Field(..., description="处理消息")
    indexedDocuments: int = Field(..., description="索引的文档数量")
    totalChunksCreated: int = Field(..., description="创建的文档块总数")
    processingTime: float = Field(..., description="处理时间（秒）")
    sessionIndexName: str = Field(..., description="会话索引名称")
    errorDetails: Optional[str] = Field(None, description="错误详情")


class SearchResponseModel(BaseModel):
    """搜索响应模型"""
    results: List[Dict[str, Any]] = Field(..., description="搜索结果列表")
    total: int = Field(..., description="总结果数量")
    took: int = Field(..., description="查询耗时(毫秒)")
    sessionId: str = Field(..., description="会话ID")
    query: str = Field(..., description="查询文本")


# API接口实现
@router.post("/index-documents", 
             response_model=IndexDocumentsResponseModel,
             summary="文档首次索引",
             description="将用户提供的一组原始文档转化为结构化、可被快速检索的向量知识库")
async def index_documents(request: IndexDocumentsRequestModel) -> IndexDocumentsResponseModel:
    """
    文档首次索引接口
    
    实现canvas.md中设计的POST /index-documents接口：
    1. 会话级文档加载与预处理
    2. 智能文本分割
    3. 向量化
    4. 会话级存储
    """
    try:
        logger.info(f"收到文档索引请求，会话: {request.sessionId}, 文档数量: {len(request.documents)}")
        
        # 转换请求格式
        documents = [
            {"documentId": doc.documentId, "content": doc.content}
            for doc in request.documents
        ]
        
        # 获取流水线并处理
        pipeline = get_document_embedding_pipeline()
        index_request = IndexDocumentsRequest(
            session_id=request.sessionId,
            documents=documents
        )
        
        response: IndexDocumentsResponse = await pipeline.index_documents(index_request)
        
        # 转换响应格式
        return IndexDocumentsResponseModel(
            status=response.status,
            message=response.message,
            indexedDocuments=response.indexed_documents,
            totalChunksCreated=response.total_chunks_created,
            processingTime=response.processing_time,
            sessionIndexName=response.session_index_name,
            errorDetails=response.error_details
        )
        
    except Exception as e:
        logger.error(f"文档索引接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档索引失败: {str(e)}")


@router.post("/search",
             response_model=SearchResponseModel,
             summary="文档检索",
             description="在会话的文档索引中进行语义搜索")
async def search_documents(request: SearchRequestModel) -> SearchResponseModel:
    """
    文档检索接口
    
    在指定会话的文档索引中进行语义搜索
    """
    try:
        logger.info(f"收到文档搜索请求，会话: {request.sessionId}, 查询: {request.query}")
        
        # 获取流水线并搜索
        pipeline = get_document_embedding_pipeline()
        search_request = SearchDocumentsRequest(
            session_id=request.sessionId,
            query=request.query,
            top_k=request.topK
        )
        
        result = await pipeline.search_documents(search_request)
        
        # 检查是否有错误
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return SearchResponseModel(
            results=result.get("results", []),
            total=result.get("total", 0),
            took=result.get("took", 0),
            sessionId=request.sessionId,
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档搜索接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档搜索失败: {str(e)}")


@router.post("/update-knowledge-base",
             response_model=IndexDocumentsResponseModel,
             summary="更新知识库",
             description="增量更新会话的文档知识库")
async def update_knowledge_base(request: UpdateKnowledgeBaseRequestModel) -> IndexDocumentsResponseModel:
    """
    更新知识库接口
    
    实现canvas.md中设计的POST /update-knowledge-base接口：
    在文档变更后，触发RAG知识库的增量更新
    """
    try:
        logger.info(f"收到知识库更新请求，会话: {request.sessionId}, 文档数量: {len(request.updatedDocuments)}")
        
        # 转换请求格式
        updated_documents = [
            {"documentId": doc.documentId, "content": doc.content}
            for doc in request.updatedDocuments
        ]
        
        # 获取流水线并更新
        pipeline = get_document_embedding_pipeline()
        update_request = UpdateKnowledgeBaseRequest(
            session_id=request.sessionId,
            updated_documents=updated_documents
        )
        
        response: IndexDocumentsResponse = await pipeline.update_knowledge_base(update_request)
        
        # 转换响应格式
        return IndexDocumentsResponseModel(
            status=response.status,
            message=response.message,
            indexedDocuments=response.indexed_documents,
            totalChunksCreated=response.total_chunks_created,
            processingTime=response.processing_time,
            sessionIndexName=response.session_index_name,
            errorDetails=response.error_details
        )
        
    except Exception as e:
        logger.error(f"知识库更新接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"知识库更新失败: {str(e)}")


@router.delete("/session/{session_id}/clear",
               summary="清空会话索引",
               description="清空指定会话的所有文档索引")
async def clear_session_index(session_id: str) -> Dict[str, Any]:
    """
    清空会话索引接口
    
    清空指定会话的所有文档索引数据
    """
    try:
        logger.info(f"收到清空会话索引请求，会话: {session_id}")
        
        # 获取流水线并清空
        pipeline = get_document_embedding_pipeline()
        success = await pipeline.clear_session_index(session_id)
        
        if success:
            return {
                "status": "success",
                "message": f"会话 {session_id} 的索引已清空",
                "sessionId": session_id
            }
        else:
            return {
                "status": "warning",
                "message": f"会话 {session_id} 的索引清空可能未完全成功",
                "sessionId": session_id
            }
        
    except Exception as e:
        logger.error(f"清空会话索引接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空会话索引失败: {str(e)}")


@router.get("/health",
            summary="健康检查",
            description="检查文档嵌入服务的健康状态")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    try:
        # 简单的健康检查 - 验证流水线可以正常初始化
        _ = get_document_embedding_pipeline()

        return {
            "status": "healthy",
            "service": "document-embedding",
            "components": {
                "document_processor": "ok",
                "embedding_service": "ok",
                "document_indexer": "ok"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail=f"服务不健康: {str(e)}")


# 导出路由器
__all__ = ["router"]
