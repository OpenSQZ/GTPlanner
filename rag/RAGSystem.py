import asyncio
from typing import List, Dict, Optional, Tuple, AsyncGenerator
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from utils.parse_markdown import parse_markdown_async
from utils.call_llm import call_llm_async, call_llm_stream_async
from utils.store_conversation import store_conversation_async
from utils.language_detection import detect_language
from utils.multilingual_utils import get_localized_prompt


class RAGSystem:
    """Retrieval-Augmented Generation system integrating with existing utilities"""

    def __init__(self):
        self.document_chunks = []  # Stores (content, embedding, metadata)
        self.embedding_dim = 384  # Compatible with common embedding models

    async def load_document(self, file_path: str) -> bool:
        """Load and process a document into chunks for retrieval"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use existing markdown parser
            parsed = await parse_markdown_async(content)

            # Create chunks from sections
            for section_title, section_content in parsed['sections'].items():
                paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]

                for para in paragraphs:
                    embedding = self._generate_embedding(para)
                    self.document_chunks.append({
                        'content': para,
                        'embedding': embedding,
                        'metadata': {
                            'source': file_path,
                            'section': section_title,
                            'length': len(para)
                        }
                    })

            return True
        except Exception as e:
            print(f"Error loading document: {e}")
            return False

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding (simulated implementation)"""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        embedding = np.zeros(self.embedding_dim, dtype=float)

        for i in range(min(len(hash_bytes), self.embedding_dim)):
            embedding[i] = hash_bytes[i] / 255.0

        return embedding.tolist()

    def _retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve most relevant document chunks using cosine similarity"""
        if not self.document_chunks:
            return []

        query_embedding = self._generate_embedding(query)
        similarities = []

        for chunk in self.document_chunks:
            sim = cosine_similarity(
                np.array([query_embedding]).reshape(1, -1),
                np.array([chunk['embedding']]).reshape(1, -1)
            )[0][0]
            similarities.append((chunk, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in similarities[:top_k]]

    # 拆分1：非流式响应（纯异步函数）
    async def generate_response(
            self,
            query: str,
            conversation_history: Optional[List[Dict]] = None,
            top_k: int = 3
    ) -> Tuple[str, List[Dict]]:
        """Generate non-streaming response using retrieved context"""
        relevant_chunks = self._retrieve_relevant_chunks(query, top_k)
        context = "\n\n".join([f"[Context Fragment]: {chunk['content']}" for chunk in relevant_chunks])
        lang = detect_language(query)

        prompt = get_localized_prompt(
            "rag_generation",
            lang,
            context=context,
            query=query,
            history=conversation_history if conversation_history else "No previous conversation"
        )

        full_response = await call_llm_async(prompt)

        # Update conversation history
        updated_history = await store_conversation_async(
            {"role": "user", "content": query},
            conversation_history
        )
        updated_history = await store_conversation_async(
            {"role": "assistant", "content": full_response},
            updated_history
        )

        return full_response, updated_history  # 这里return是合法的

    # 拆分2：流式响应（异步生成器）
    async def generate_response_stream(
            self,
            query: str,
            conversation_history: Optional[List[Dict]] = None,
            top_k: int = 3
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using retrieved context"""
        relevant_chunks = self._retrieve_relevant_chunks(query, top_k)
        context = "\n\n".join([f"[Context Fragment]: {chunk['content']}" for chunk in relevant_chunks])
        lang = detect_language(query)

        prompt = get_localized_prompt(
            "rag_generation",
            lang,
            context=context,
            query=query,
            history=conversation_history if conversation_history else "No previous conversation"
        )

        response_chunks = []
        async for chunk in call_llm_stream_async(prompt):
            response_chunks.append(chunk)
            yield chunk  # 异步生成器中只能yield

        # 流式响应结束后更新对话历史（注意：这里不返回值，只做副作用操作）
        full_response = ''.join(response_chunks)
        updated_history = await store_conversation_async(
            {"role": "user", "content": query},
            conversation_history
        )
        await store_conversation_async(
            {"role": "assistant", "content": full_response},
            updated_history
        )


# Example usage
if __name__ == "__main__":
    async def test_rag():
        rag = RAGSystem()

        # Load example document
        await rag.load_document("example_documentation.md")

        # Test non-streaming response
        query = "What are the key requirements?"
        response, history = await rag.generate_response(query)
        print("Query:", query)
        print("Response:", response)
        print("Conversation History Length:", len(history))

        # Test streaming response
        print("\nStreaming response:")
        async for chunk in rag.generate_response_stream("Explain the optimizations"):
            print(chunk, end='', flush=True)


    asyncio.run(test_rag())
