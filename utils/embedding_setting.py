import os
from typing import Any, List, Optional, Union

from langchain_core.embeddings import Embeddings
from openai import OpenAI


class DashScopeEmbeddings(Embeddings):
    """阿里云百炼服务的Embeddings实现，兼容LangChain接口"""

    def __init__(
        self,
        model: str = "text-embedding-v4",
        dimensions: int = 1024,
        encoding_format: str = "float",
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        """
        初始化DashScope嵌入模型

        Args:
            model: 模型名称，默认为"text-embedding-v4"
            dimensions: 向量维度（仅v3/v4支持）
            encoding_format: 编码格式，默认为"float"
            api_key: 阿里云API Key，如未提供将从环境变量DASHSCOPE_API_KEY读取
            base_url: API基础URL
        """
        self.model = model
        self.dimensions = dimensions
        self.encoding_format = encoding_format
        self.api_key = api_key
        self.base_url = base_url

        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表生成嵌入向量

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表，每个向量是一个浮点数列表
        """
        # 过滤空文本
        texts = [text for text in texts if text and isinstance(text, str)]
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
            encoding_format=self.encoding_format,
        )

        # 提取嵌入向量
        return [embedding.embedding for embedding in response.data]

    def embed_query(self, text: str) -> List[float]:
        """为单个查询文本生成嵌入向量

        Args:
            text: 要嵌入的查询文本

        Returns:
            嵌入向量，是一个浮点数列表
        """
        if not text or not isinstance(text, str):
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
            dimensions=self.dimensions,
            encoding_format=self.encoding_format,
        )

        return response.data[0].embedding

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步为文档列表生成嵌入向量"""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """异步为单个查询文本生成嵌入向量"""
        return self.embed_query(text)