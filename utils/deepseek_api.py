"""
DeepSeek API集成模块

提供与DeepSeek API的集成功能，用于RAG系统的LLM调用。
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekAPI:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        """
        初始化DeepSeek API客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            base_url: API基础URL
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_api_key_from_env(self) -> str:
        """从环境变量获取API密钥"""
        import os
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key not found. Please set DEEPSEEK_API_KEY environment variable.")
        return api_key
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "deepseek-chat",
                       temperature: float = 0.7,
                       max_tokens: int = 1000) -> Dict[str, Any]:
        """
        调用DeepSeek聊天完成API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            
        Returns:
            Dict[str, Any]: API响应
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise Exception(f"DeepSeek API request failed: {e}")
    
    def generate_response(self, 
                         prompt: str, 
                         context: str = "", 
                         system_prompt: str = None) -> str:
        """
        生成回答
        
        Args:
            prompt: 用户问题
            context: 上下文信息
            system_prompt: 系统提示词
            
        Returns:
            str: 生成的回答
        """
        # 构建消息列表
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 构建用户消息
        user_content = prompt
        if context:
            user_content = f"基于以下上下文信息回答问题：\n\n上下文：{context}\n\n问题：{prompt}"
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            # 调用API
            response = self.chat_completion(messages)
            
            # 提取回答
            if "choices" in response and len(response["choices"]) > 0:
                answer = response["choices"][0]["message"]["content"]
                return answer
            else:
                logger.error(f"Unexpected API response format: {response}")
                return "抱歉，无法生成回答。"
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"生成回答时出错：{str(e)}"


class DeepSeekRAGEngine:
    """基于DeepSeek的RAG引擎"""
    
    def __init__(self, knowledge_base, retriever, api_key: str = None):
        """
        初始化DeepSeek RAG引擎
        
        Args:
            knowledge_base: 知识库实例
            retriever: 检索器实例
            api_key: DeepSeek API密钥
        """
        self.knowledge_base = knowledge_base
        self.retriever = retriever
        self.deepseek_api = DeepSeekAPI(api_key)
        
        # 默认系统提示词
        self.default_system_prompt = """你是一个智能助手，基于提供的上下文信息回答问题。
请确保回答准确、完整，如果上下文信息不足以回答问题，请明确说明。"""
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        执行RAG查询
        
        Args:
            question: 用户问题
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            # 1. 检索相关文档
            relevant_docs = self.retriever.retrieve(question)
            
            # 2. 构建上下文
            context = self._build_context(relevant_docs)
            
            # 3. 调用DeepSeek API生成回答
            answer = self.deepseek_api.generate_response(
                prompt=question,
                context=context,
                system_prompt=self.default_system_prompt
            )
            
            return {
                "question": question,
                "answer": answer,
                "relevant_documents": [doc.to_dict() for doc in relevant_docs],
                "document_count": len(relevant_docs),
                "context": context
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                "question": question,
                "answer": f"查询失败：{str(e)}",
                "relevant_documents": [],
                "document_count": 0,
                "context": ""
            }
    
    def _build_context(self, documents: List) -> str:
        """
        构建上下文信息
        
        Args:
            documents: 相关文档列表
            
        Returns:
            str: 上下文信息
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
            metadata: 元数据
            
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
        total_docs = self.knowledge_base.get_document_count()
        all_docs = self.knowledge_base.get_all_documents()
        
        total_keywords = 0
        for doc in all_docs:
            total_keywords += len(doc.get_keywords())
        
        return {
            "total_documents": total_docs,
            "total_keywords": total_keywords,
            "average_keywords_per_doc": total_keywords / total_docs if total_docs > 0 else 0
        }


# 兼容性函数，用于替换原有的mock_llm_api
def deepseek_llm_api(prompt: str, context: str = "") -> str:
    """
    兼容性函数，用于替换原有的mock_llm_api
    
    Args:
        prompt: 用户问题
        context: 上下文信息
        
    Returns:
        str: 生成的回答
    """
    try:
        api = DeepSeekAPI()
        return api.generate_response(prompt, context)
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        return f"API调用失败：{str(e)}" 