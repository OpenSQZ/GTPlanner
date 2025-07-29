"""
RAG系统测试用例
"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from utils.rag_system import (
    Document,
    KnowledgeBase,
    SimpleKeywordRetriever,
    RAGEngine,
    mock_llm_api
)


class TestDocument:
    """测试Document类"""
    
    def test_document_creation(self):
        """测试Document对象创建"""
        doc = Document(
            id="test_001",
            title="测试文档",
            content="这是一个测试文档的内容",
            metadata={"category": "test"},
            created_at="2024-01-01T00:00:00"
        )
        
        assert doc.id == "test_001"
        assert doc.title == "测试文档"
        assert doc.content == "这是一个测试文档的内容"
        assert doc.metadata["category"] == "test"
        assert doc.created_at == "2024-01-01T00:00:00"
    
    def test_document_validation_empty_id(self):
        """测试空ID验证"""
        with pytest.raises(ValueError, match="Document id cannot be empty"):
            Document(
                id="",
                title="测试文档",
                content="内容",
                metadata={},
                created_at="2024-01-01T00:00:00"
            )
    
    def test_document_validation_empty_title(self):
        """测试空标题验证"""
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(
                id="test_001",
                title="",
                content="内容",
                metadata={},
                created_at="2024-01-01T00:00:00"
            )
    
    def test_document_validation_empty_content(self):
        """测试空内容验证"""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                id="test_001",
                title="测试文档",
                content="",
                metadata={},
                created_at="2024-01-01T00:00:00"
            )
    
    def test_document_keywords_extraction(self):
        """测试关键词提取"""
        doc = Document(
            id="test_001",
            title="Python编程指南",
            content="Python是一种高级编程语言，广泛应用于数据科学和人工智能领域。",
            metadata={},
            created_at="2024-01-01T00:00:00"
        )
        
        keywords = doc.get_keywords()
        assert "Python" in keywords
        assert any("编程" in kw for kw in keywords)
        assert any("语言" in kw for kw in keywords)
    
    def test_document_to_dict(self):
        """测试转换为字典"""
        doc = Document(
            id="test_001",
            title="测试文档",
            content="内容",
            metadata={"category": "test"},
            created_at="2024-01-01T00:00:00"
        )
        
        doc_dict = doc.to_dict()
        assert doc_dict["id"] == "test_001"
        assert doc_dict["title"] == "测试文档"
        assert doc_dict["content"] == "内容"
        assert doc_dict["metadata"]["category"] == "test"


class TestKnowledgeBase:
    """测试KnowledgeBase类"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def knowledge_base(self, temp_file):
        """创建知识库实例"""
        return KnowledgeBase(temp_file)
    
    def test_knowledge_base_initialization(self, temp_file):
        """测试知识库初始化"""
        kb = KnowledgeBase(temp_file)
        assert str(kb.storage_path) == temp_file
        assert len(kb.documents) == 0
    
    def test_add_document(self, knowledge_base):
        """测试添加文档"""
        doc_id = knowledge_base.add_document(
            title="测试文档",
            content="这是测试内容",
            metadata={"category": "test"}
        )
        
        assert doc_id is not None
        assert len(knowledge_base.documents) == 1
        
        doc = knowledge_base.get_document(doc_id)
        assert doc is not None
        assert doc.title == "测试文档"
        assert doc.content == "这是测试内容"
        assert doc.metadata["category"] == "test"
    
    def test_get_document(self, knowledge_base):
        """测试获取文档"""
        doc_id = knowledge_base.add_document("测试文档", "测试内容")
        doc = knowledge_base.get_document(doc_id)
        
        assert doc is not None
        assert doc.title == "测试文档"
        
        # 测试获取不存在的文档
        non_existent = knowledge_base.get_document("non_existent")
        assert non_existent is None
    
    def test_get_all_documents(self, knowledge_base):
        """测试获取所有文档"""
        knowledge_base.add_document("文档1", "内容1")
        knowledge_base.add_document("文档2", "内容2")
        
        docs = knowledge_base.get_all_documents()
        assert len(docs) == 2
        assert any(doc.title == "文档1" for doc in docs)
        assert any(doc.title == "文档2" for doc in docs)
    
    def test_search_documents(self, knowledge_base):
        """测试搜索文档"""
        knowledge_base.add_document("Python编程", "Python是一种编程语言")
        knowledge_base.add_document("Java编程", "Java是另一种编程语言")
        knowledge_base.add_document("数据结构", "数据结构是计算机科学的基础")
        
        # 搜索包含"编程"的文档
        results = knowledge_base.search_documents("编程")
        assert len(results) == 2
        assert any("Python" in doc.title for doc in results)
        assert any("Java" in doc.title for doc in results)
        
        # 搜索包含"Python"的文档
        results = knowledge_base.search_documents("Python")
        assert len(results) == 1
        assert "Python" in results[0].title
    
    def test_remove_document(self, knowledge_base):
        """测试删除文档"""
        doc_id = knowledge_base.add_document("测试文档", "测试内容")
        assert len(knowledge_base.documents) == 1
        
        # 删除文档
        success = knowledge_base.remove_document(doc_id)
        assert success is True
        assert len(knowledge_base.documents) == 0
        
        # 删除不存在的文档
        success = knowledge_base.remove_document("non_existent")
        assert success is False
    
    def test_get_document_count(self, knowledge_base):
        """测试获取文档数量"""
        assert knowledge_base.get_document_count() == 0
        
        knowledge_base.add_document("文档1", "内容1")
        assert knowledge_base.get_document_count() == 1
        
        knowledge_base.add_document("文档2", "内容2")
        assert knowledge_base.get_document_count() == 2


class TestSimpleKeywordRetriever:
    """测试SimpleKeywordRetriever类"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def knowledge_base(self, temp_file):
        """创建知识库实例"""
        kb = KnowledgeBase(temp_file)
        # 添加测试文档
        kb.add_document("Python编程基础", "Python是一种高级编程语言，语法简洁易学")
        kb.add_document("机器学习入门", "机器学习是人工智能的一个重要分支，使用算法训练模型")
        kb.add_document("数据结构与算法", "数据结构是计算机科学的基础，包括数组、链表、树等")
        return kb
    
    @pytest.fixture
    def retriever(self, knowledge_base):
        """创建检索器实例"""
        return SimpleKeywordRetriever(knowledge_base, top_k=2)
    
    def test_retriever_initialization(self, knowledge_base):
        """测试检索器初始化"""
        retriever = SimpleKeywordRetriever(knowledge_base, top_k=5)
        assert retriever.knowledge_base == knowledge_base
        assert retriever.top_k == 5
    
    def test_retrieve_python_query(self, retriever):
        """测试Python相关查询"""
        docs = retriever.retrieve("Python编程")
        assert len(docs) > 0
        assert any("Python" in doc.title for doc in docs)
    
    def test_retrieve_machine_learning_query(self, retriever):
        """测试机器学习相关查询"""
        docs = retriever.retrieve("机器学习算法")
        assert len(docs) > 0
        assert any("机器学习" in doc.title for doc in docs)
    
    def test_retrieve_data_structure_query(self, retriever):
        """测试数据结构相关查询"""
        docs = retriever.retrieve("数据结构")
        assert len(docs) > 0
        assert any("数据结构" in doc.title for doc in docs)
    
    def test_retrieve_empty_query(self, retriever):
        """测试空查询"""
        docs = retriever.retrieve("")
        assert len(docs) == 0
    
    def test_retrieve_unrelated_query(self, retriever):
        """测试无关查询"""
        docs = retriever.retrieve("完全不相关的内容")
        assert len(docs) == 0
    
    def test_extract_keywords(self, retriever):
        """测试关键词提取"""
        keywords = retriever._extract_keywords("Python编程语言")
        assert "Python" in keywords
        assert any("编程" in kw for kw in keywords)
        assert any("语言" in kw for kw in keywords)
    
    def test_calculate_relevance_score(self, retriever, knowledge_base):
        """测试相关性分数计算"""
        doc = knowledge_base.get_all_documents()[0]  # 获取第一个文档
        score = retriever._calculate_relevance_score(["Python", "编程"], doc)
        assert score > 0


class TestRAGEngine:
    """测试RAGEngine类"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def rag_engine(self, temp_file):
        """创建RAG引擎实例"""
        kb = KnowledgeBase(temp_file)
        retriever = SimpleKeywordRetriever(kb, top_k=2)
        return RAGEngine(kb, retriever)
    
    def test_rag_engine_initialization(self, temp_file):
        """测试RAG引擎初始化"""
        kb = KnowledgeBase(temp_file)
        retriever = SimpleKeywordRetriever(kb)
        engine = RAGEngine(kb, retriever)
        
        assert engine.knowledge_base == kb
        assert engine.retriever == retriever
        assert engine.llm_function is not None
    
    def test_query_with_documents(self, rag_engine):
        """测试有文档的查询"""
        # 添加文档
        rag_engine.add_document("Python基础", "Python是一种编程语言，语法简洁")
        rag_engine.add_document("机器学习", "机器学习是AI的重要分支")
        
        # 查询
        result = rag_engine.query("什么是Python？")
        
        assert "question" in result
        assert "answer" in result
        assert "relevant_documents" in result
        assert "document_count" in result
        assert result["question"] == "什么是Python？"
        assert len(result["answer"]) > 0
        assert result["document_count"] > 0
    
    def test_query_without_documents(self, rag_engine):
        """测试无文档的查询"""
        result = rag_engine.query("什么是Python？")
        
        assert "question" in result
        assert "answer" in result
        assert "relevant_documents" in result
        assert "document_count" in result
        assert result["document_count"] == 0
        assert len(result["answer"]) > 0
    
    def test_add_document_through_engine(self, rag_engine):
        """测试通过引擎添加文档"""
        doc_id = rag_engine.add_document("测试文档", "测试内容")
        assert doc_id is not None
        
        # 验证文档已添加到知识库
        doc = rag_engine.knowledge_base.get_document(doc_id)
        assert doc is not None
        assert doc.title == "测试文档"
    
    def test_get_knowledge_base_stats(self, rag_engine):
        """测试获取知识库统计信息"""
        # 添加一些文档
        rag_engine.add_document("文档1", "内容1")
        rag_engine.add_document("文档2", "内容2")
        
        stats = rag_engine.get_knowledge_base_stats()
        
        assert "total_documents" in stats
        assert "total_keywords" in stats
        assert "average_keywords_per_doc" in stats
        assert "storage_path" in stats
        assert stats["total_documents"] == 2
        assert stats["total_keywords"] > 0
        assert stats["average_keywords_per_doc"] > 0
    
    def test_build_context(self, rag_engine):
        """测试构建上下文"""
        # 创建测试文档
        doc1 = Document(
            id="1",
            title="文档1",
            content="内容1",
            metadata={},
            created_at="2024-01-01T00:00:00"
        )
        doc2 = Document(
            id="2",
            title="文档2",
            content="内容2",
            metadata={},
            created_at="2024-01-01T00:00:00"
        )
        
        context = rag_engine._build_context([doc1, doc2])
        assert "文档1" in context
        assert "内容1" in context
        assert "文档2" in context
        assert "内容2" in context
    
    def test_build_empty_context(self, rag_engine):
        """测试构建空上下文"""
        context = rag_engine._build_context([])
        assert context == ""


class TestMockLLMAPI:
    """测试模拟LLM API"""
    
    def test_mock_llm_api_with_context(self):
        """测试带上下文的模拟API"""
        answer = mock_llm_api("什么是Python？", "Python是一种编程语言")
        assert "Python" in answer
        assert "编程语言" in answer
    
    def test_mock_llm_api_without_context(self):
        """测试不带上下文的模拟API"""
        answer = mock_llm_api("什么是Python？")
        assert "Python" in answer
        assert "一般性信息" in answer


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    def test_full_rag_workflow(self, temp_file):
        """测试完整的RAG工作流程"""
        # 1. 初始化组件
        kb = KnowledgeBase(temp_file)
        retriever = SimpleKeywordRetriever(kb, top_k=2)
        engine = RAGEngine(kb, retriever)
        
        # 2. 添加文档
        engine.add_document("Python编程", "Python是一种高级编程语言，语法简洁易学")
        engine.add_document("机器学习", "机器学习是人工智能的重要分支，使用算法训练模型")
        engine.add_document("数据结构", "数据结构是计算机科学的基础，包括数组、链表等")
        
        # 3. 查询
        result = engine.query("什么是Python编程？")
        
        # 4. 验证结果
        assert result["question"] == "什么是Python编程？"
        assert len(result["answer"]) > 0
        assert result["document_count"] > 0
        assert len(result["relevant_documents"]) > 0
        
        # 5. 验证统计信息
        stats = engine.get_knowledge_base_stats()
        assert stats["total_documents"] == 3
        assert stats["total_keywords"] > 0 