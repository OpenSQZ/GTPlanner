import asyncio
import re
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import aiohttp
import json
from dynaconf import Dynaconf

# Initialize settings
settings = Dynaconf(
    settings_files=["settings.toml", "settings.local.toml", ".secrets.toml"],
    environments=True,
    env_switcher="ENV_FOR_DYNACONF",
    load_dotenv=True,
)


class TokenCounter:
    """Simple token counter for text chunking."""
    
    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Simple token counting approximation.
        Uses word count * 1.3 as rough estimate for GPT tokens.
        For production, consider using tiktoken library.
        """
        if not text:
            return 0
        
        # Split by whitespace and punctuation for better estimation
        words = re.findall(r'\w+', text)
        return int(len(words) * 1.3)
    
    @staticmethod
    def chunk_text_by_tokens(text: str, max_tokens: int) -> List[str]:
        """
        Split text into chunks of approximately max_tokens each.
        Tries to break on sentence boundaries when possible.
        """
        if not text:
            return []
        
        if TokenCounter.count_tokens(text) <= max_tokens:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = re.split(r'[.!?]+\s*', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence = sentence.strip() + '. '
            sentence_tokens = TokenCounter.count_tokens(sentence)
            current_chunk_tokens = TokenCounter.count_tokens(current_chunk)
            
            # If adding this sentence would exceed max_tokens
            if current_chunk_tokens + sentence_tokens > max_tokens:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        temp_tokens = TokenCounter.count_tokens(temp_chunk + " " + word)
                        if temp_tokens > max_tokens and temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            temp_chunk += " " + word if temp_chunk else word
                    if temp_chunk.strip():
                        current_chunk = temp_chunk
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


class MessageChunk:
    """Represents a chunk of a conversation message."""
    
    def __init__(self, role: str, content: str, embedding: Optional[List[float]] = None, 
                 timestamp: Optional[int] = None, message_type: str = "message", 
                 chunk_index: int = 0, total_chunks: int = 1):
        self.role = role
        self.content = content
        self.embedding = embedding
        self.timestamp = timestamp or int(time.time())
        self.message_type = message_type
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "embedding": self.embedding,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks
        }


class EmbeddingService:
    """Service for generating embeddings using OpenAI API."""
    
    def __init__(self):
        self.model = "text-embedding-3-small"  # More cost-effective model
        self.base_url = getattr(settings.llm, 'base_url', 'https://api.openai.com/v1')
        self.api_key = getattr(settings.llm, 'api_key', '')
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using OpenAI API.
        """
        if not texts:
            return []
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=30)
                async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Embedding API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    embeddings = [item["embedding"] for item in data["data"]]
                    return embeddings
        
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * 1536 for _ in texts]  # text-embedding-3-small has 1536 dimensions
    
    async def get_single_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * 1536


class SimilarityCalculator:
    """Calculate cosine similarity between embeddings."""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    @staticmethod
    def find_top_k_similar(query_embedding: List[float], 
                          chunk_embeddings: List[Tuple[MessageChunk, List[float]]], 
                          k: int = 10) -> List[Tuple[MessageChunk, float]]:
        """
        Find top k most similar chunks to the query.
        Returns list of (chunk, similarity_score) tuples.
        """
        if not query_embedding or not chunk_embeddings:
            return []
        
        similarities = []
        for chunk, embedding in chunk_embeddings:
            similarity = SimilarityCalculator.cosine_similarity(query_embedding, embedding)
            similarities.append((chunk, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]


class ConversationContextManager:
    """Main class for managing conversation context optimization."""
    
    def __init__(self, chunk_size_tokens: int = 200, top_k: int = 15):
        self.chunk_size_tokens = chunk_size_tokens
        self.top_k = top_k
        self.token_counter = TokenCounter()
        self.embedding_service = EmbeddingService()
        self.similarity_calculator = SimilarityCalculator()
    
    async def chunk_messages(self, messages: List[Dict[str, Any]]) -> List[MessageChunk]:
        """
        Convert conversation messages into fixed-size token chunks.
        """
        chunks = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            timestamp = message.get("timestamp", int(time.time()))
            message_type = message.get("message_type", "message")
            
            if not content.strip():
                continue
            
            # Split content into chunks
            content_chunks = self.token_counter.chunk_text_by_tokens(
                content, self.chunk_size_tokens
            )
            
            total_chunks = len(content_chunks)
            for i, chunk_content in enumerate(content_chunks):
                chunk = MessageChunk(
                    role=role,
                    content=chunk_content,
                    timestamp=timestamp,
                    message_type=message_type,
                    chunk_index=i,
                    total_chunks=total_chunks
                )
                chunks.append(chunk)
        
        return chunks
    
    async def add_embeddings_to_chunks(self, chunks: List[MessageChunk]) -> List[MessageChunk]:
        """
        Add embeddings to message chunks using batch processing for efficiency.
        """
        if not chunks:
            return []
        
        # Extract content for embedding
        texts = [chunk.content for chunk in chunks]
        
        # Get embeddings in batch
        embeddings = await self.embedding_service.get_embeddings(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        return chunks
    
    async def retrieve_relevant_context(self, current_message: str, 
                                      chunks: List[MessageChunk]) -> Tuple[str, Dict[str, Any]]:
        """
        Retrieve most relevant chunks based on similarity to current message.
        """
        if not chunks:
            return "", {"total_chunks": 0, "selected_chunks": 0, "compression_ratio": 1.0}
        
        # Get embedding for current message
        query_embedding = await self.embedding_service.get_single_embedding(current_message)
        
        # Calculate similarities and get top k
        chunk_embeddings = [(chunk, chunk.embedding) for chunk in chunks if chunk.embedding]
        top_chunks = self.similarity_calculator.find_top_k_similar(
            query_embedding, chunk_embeddings, self.top_k
        )
        
        # Build context string from most relevant chunks
        context_parts = []
        for chunk, similarity in top_chunks:
            # Format: [role] content (similarity: score)
            context_parts.append(f"[{chunk.role}] {chunk.content}")
        
        context_str = "\n".join(context_parts)
        
        # Calculate statistics
        total_chunks = len(chunks)
        selected_chunks = len(top_chunks)
        compression_ratio = selected_chunks / total_chunks if total_chunks > 0 else 1.0
        
        stats = {
            "total_chunks": total_chunks,
            "selected_chunks": selected_chunks,
            "compression_ratio": compression_ratio,
            "avg_similarity": sum(score for _, score in top_chunks) / len(top_chunks) if top_chunks else 0.0,
            "chunk_size_tokens": self.chunk_size_tokens,
            "top_k": self.top_k
        }
        
        return context_str, stats


# Global instance
context_manager = ConversationContextManager()


async def optimize_conversation_context(conversation_history: List[Dict[str, Any]], 
                                      current_message: str,
                                      chunk_size_tokens: int = 200,
                                      top_k: int = 15) -> Tuple[str, Dict[str, Any]]:
    """
    Main function to optimize conversation context using embeddings and similarity search.
    
    Args:
        conversation_history: List of message dictionaries with keys: role, content, message_type, timestamp
        current_message: The current user message to find relevant context for
        chunk_size_tokens: Maximum tokens per chunk
        top_k: Number of most similar chunks to retrieve
    
    Returns:
        Tuple of (context_string, statistics_dict)
    """
    try:
        # Create context manager with specified parameters
        manager = ConversationContextManager(chunk_size_tokens, top_k)
        
        # Step 1: Convert messages to fixed-size chunks
        chunks = await manager.chunk_messages(conversation_history)
        
        if not chunks:
            return "", {"error": "No valid chunks created from conversation history"}
        
        # Step 2: Add embeddings to chunks
        chunks_with_embeddings = await manager.add_embeddings_to_chunks(chunks)
        
        # Step 3: Retrieve most relevant chunks
        context_str, stats = await manager.retrieve_relevant_context(
            current_message, chunks_with_embeddings
        )
        
        return context_str, stats
        
    except Exception as e:
        print(f"上下文优化失败，使用降级策略: {e}")
        # Fallback: return simple concatenation of recent messages
        fallback_context = "\n".join([
            f"[{msg.get('role', 'user')}] {msg.get('content', '')}"
            for msg in conversation_history[-5:]  # Last 5 messages
            if msg.get('content', '').strip()
        ])
        
        return fallback_context, {
            "error": str(e),
            "fallback_used": True,
            "fallback_messages": min(5, len(conversation_history))
        } 