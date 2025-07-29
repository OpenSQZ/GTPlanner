"""
简化RAG（检索增强生成）系统

提供文档管理、关键词检索和RAG引擎功能。
"""

import json
import jieba
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档类，表示知识库中的单个文档"""
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    
    def __post_init__(self):
        """验证数据完整性"""
        if not self.id.strip():
            raise ValueError("Document id cannot be empty")
        if not self.title.strip():
            raise ValueError("Document title cannot be empty")
        if not self.content.strip():
            raise ValueError("Document content cannot be empty")
        if not self.created_at.strip():
            raise ValueError("Document created_at cannot be empty")
    
    def get_keywords(self) -> List[str]:
        """
        提取文档关键词
        
        Returns:
            List[str]: 关键词列表
        """
        # 使用jieba分词
        words = jieba.cut(self.content)
        # 过滤停用词和短词
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and not re.match(r'^[^\u4e00-\u9fa5a-zA-Z0-9]+$', word):
                keywords.append(word)
        return keywords
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class KnowledgeBase:
    """知识库类，管理文档集合"""
    
    def __init__(self, storage_path: str = "knowledge_base.json"):
        """
        初始化知识库
        
        Args:
            storage_path: 存储文件路径
        """
        self.storage_path = Path(storage_path)
        self.documents: Dict[str, Document] = {}
        self._load_documents()
    
    def _load_documents(self) -> None:
        """从文件加载文档"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(**doc_data)
                        self.documents[doc.id] = doc
                logger.info(f"Loaded {len(self.documents)} documents from {self.storage_path}")
            else:
                logger.info(f"Knowledge base file not found, creating new one: {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.documents = {}
    
    def _save_documents(self) -> None:
        """保存文档到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([doc.to_dict() for doc in self.documents.values()], 
                         f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.documents)} documents to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
            raise
    
    def add_document(self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加文档到知识库
        
        Args:
            title: 文档标题
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            str: 文档ID
        """
        try:
            doc_id = f"doc_{len(self.documents) + 1}_{int(datetime.now().timestamp())}"
            doc = Document(
                id=doc_id,
                title=title,
                content=content,
                metadata=metadata or {},
                created_at=datetime.now().isoformat()
            )
            
            self.documents[doc_id] = doc
            self._save_documents()
            logger.info(f"Added document: {title}")
            return doc_id
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Document]: 文档对象，如果不存在则返回None
        """
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[Document]:
        """
        获取所有文档
        
        Returns:
            List[Document]: 文档列表
        """
        return list(self.documents.values())
    
    def search_documents(self, query: str) -> List[Document]:
        """
        搜索文档（简单实现，基于标题和内容包含查询）
        
        Args:
            query: 搜索查询
            
        Returns:
            List[Document]: 匹配的文档列表
        """
        query_lower = query.lower()
        results = []
        
        for doc in self.documents.values():
            if (query_lower in doc.title.lower() or 
                query_lower in doc.content.lower()):
                results.append(doc)
        
        return results
    
    def remove_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 删除是否成功
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_documents()
            logger.info(f"Removed document: {doc_id}")
            return True
        return False
    
    def get_document_count(self) -> int:
        """
        获取文档数量
        
        Returns:
            int: 文档数量
        """
        return len(self.documents)


class SimpleKeywordRetriever:
    """基于关键词匹配的检索器"""
    
    def __init__(self, knowledge_base: KnowledgeBase, top_k: int = 3):
        """
        初始化检索器
        
        Args:
            knowledge_base: 知识库实例
            top_k: 返回的文档数量
        """
        self.knowledge_base = knowledge_base
        self.top_k = top_k
    
    def retrieve(self, query: str) -> List[Document]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            
        Returns:
            List[Document]: 相关文档列表
        """
        try:
            # 对查询进行分词
            query_keywords = self._extract_keywords(query)
            if not query_keywords:
                return []
            
            # 计算每个文档的相关性分数
            doc_scores = []
            for doc in self.knowledge_base.get_all_documents():
                score = self._calculate_relevance_score(query_keywords, doc)
                if score > 0:
                    doc_scores.append((doc, score))
            
            # 按分数排序并返回top_k个文档
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, score in doc_scores[:self.top_k]]
            
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        words = jieba.cut(text)
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and not re.match(r'^[^\u4e00-\u9fa5a-zA-Z0-9]+$', word):
                keywords.append(word)
        return keywords
    
    def _calculate_relevance_score(self, query_keywords: List[str], doc: Document) -> float:
        """
        计算文档相关性分数
        
        Args:
            query_keywords: 查询关键词
            doc: 文档对象
            
        Returns:
            float: 相关性分数
        """
        doc_keywords = doc.get_keywords()
        doc_text = f"{doc.title} {doc.content}".lower()
        
        score = 0.0
        
        # 计算关键词匹配分数
        for keyword in query_keywords:
            # 标题匹配权重更高
            if keyword in doc.title.lower():
                score += 2.0
            # 内容匹配
            if keyword in doc_text:
                score += 1.0
            # 精确关键词匹配
            if keyword in doc_keywords:
                score += 0.5
        
        return score


def mock_llm_api(prompt: str, context: str = "") -> str:
    """
    模拟LLM API调用
    
    Args:
        prompt: 用户提示
        context: 上下文信息
        
    Returns:
        str: 生成的回答
    """
    # 模拟API延迟
    import time
    time.sleep(0.1)
    
    if context:
        return f"基于提供的上下文信息：{context[:100]}...\n\n回答：{prompt}的相关信息如上所示。"
    else:
        return f"这是对'{prompt}'的回答。由于没有相关上下文，我只能提供一般性信息。"


class RAGEngine:
    """RAG引擎，整合检索和生成逻辑"""
    
    def __init__(self, knowledge_base: KnowledgeBase, retriever: SimpleKeywordRetriever, 
                 llm_function=None):
        """
        初始化RAG引擎
        
        Args:
            knowledge_base: 知识库实例
            retriever: 检索器实例
            llm_function: LLM调用函数，默认为mock_llm_api
        """
        self.knowledge_base = knowledge_base
        self.retriever = retriever
        self.llm_function = llm_function or mock_llm_api
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            question: 用户问题
            
        Returns:
            Dict[str, Any]: 包含回答和相关文档的结果
        """
        try:
            # 1. 检索相关文档
            relevant_docs = self.retriever.retrieve(question)
            
            # 2. 构建上下文
            context = self._build_context(relevant_docs)
            
            # 3. 生成回答
            answer = self.llm_function(question, context)
            
            # 4. 返回结果
            return {
                "question": question,
                "answer": answer,
                "relevant_documents": [doc.to_dict() for doc in relevant_docs],
                "document_count": len(relevant_docs),
                "context_length": len(context)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "question": question,
                "answer": f"抱歉，处理您的问题时出现错误：{str(e)}",
                "relevant_documents": [],
                "document_count": 0,
                "context_length": 0,
                "error": str(e)
            }
    
    def _build_context(self, documents: List[Document]) -> str:
        """
        构建上下文字符串
        
        Args:
            documents: 相关文档列表
            
        Returns:
            str: 上下文字符串
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"文档{i} - {doc.title}:\n{doc.content}")
        
        return "\n\n".join(context_parts)
    
    def add_document(self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加文档到知识库
        
        Args:
            title: 文档标题
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            str: 文档ID
        """
        return self.knowledge_base.add_document(title, content, metadata)
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        docs = self.knowledge_base.get_all_documents()
        total_keywords = sum(len(doc.get_keywords()) for doc in docs)
        
        return {
            "total_documents": len(docs),
            "total_keywords": total_keywords,
            "average_keywords_per_doc": total_keywords / len(docs) if docs else 0,
            "storage_path": str(self.knowledge_base.storage_path)
        } 