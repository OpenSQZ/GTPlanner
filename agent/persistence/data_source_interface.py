"""
数据源抽象接口

定义压缩器所需的数据访问接口，支持多种数据源（SQLite、Redis、MongoDB、MySQL等）
所有方法都是异步的，防止阻塞事件循环
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import asyncio


class DataSourceInterface(ABC):
    """数据源抽象接口"""
    
    @abstractmethod
    async def get_active_compressed_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取活跃的压缩上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            压缩上下文数据或None
        """
        pass
    
    @abstractmethod
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        Args:
            session_id: 会话ID
            limit: 限制数量
            
        Returns:
            消息列表
        """
        pass
    
    @abstractmethod
    async def get_compressed_contexts(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取压缩上下文版本列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            压缩上下文版本列表
        """
        pass
    
    @abstractmethod
    async def save_compressed_context(self, session_id: str, compressed_data: Dict[str, Any],
                               version: int, compression_ratio: float,
                               metadata: Dict[str, Any]) -> bool:
        """
        保存压缩结果
        
        Args:
            session_id: 会话ID
            compressed_data: 压缩数据
            version: 版本号
            compression_ratio: 压缩比
            metadata: 元数据
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> bool:
        """
        加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否加载成功
        """
        pass


class SQLiteDataSourceAdapter(DataSourceInterface):
    """SQLite数据源适配器"""
    
    def __init__(self, session_manager):
        """
        初始化SQLite适配器
        
        Args:
            session_manager: SQLiteSessionManager实例
        """
        self.session_manager = session_manager
        self.dao = session_manager.dao
    
    async def get_active_compressed_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取活跃的压缩上下文"""
        return await asyncio.to_thread(self.dao.get_active_compressed_context, session_id)
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取会话消息"""
        return await asyncio.to_thread(self.dao.get_messages, session_id, limit)
    
    async def get_compressed_contexts(self, session_id: str) -> List[Dict[str, Any]]:
        """获取压缩上下文版本列表"""
        return await asyncio.to_thread(self.dao.get_compressed_contexts, session_id)
    
    async def save_compressed_context(self, session_id: str, compressed_data: Dict[str, Any],
                               version: int, compression_ratio: float,
                               metadata: Dict[str, Any]) -> bool:
        """保存压缩结果"""
        return await asyncio.to_thread(
            self.dao.save_compressed_context,
            session_id=session_id,
            compressed_data=compressed_data,
            version=version,
            compression_ratio=compression_ratio,
            metadata=metadata
        )
    
    async def load_session(self, session_id: str) -> bool:
        """加载会话"""
        return await asyncio.to_thread(self.session_manager.load_session, session_id)


class RedisDataSource(DataSourceInterface):
    """Redis数据源（示例实现）"""
    
    def __init__(self, redis_client):
        """
        初始化Redis适配器
        
        Args:
            redis_client: Redis客户端实例
        """
        self.redis_client = redis_client
    
    async def get_active_compressed_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取活跃的压缩上下文"""
        # TODO: 实现Redis异步数据访问逻辑
        raise NotImplementedError("Redis适配器待实现")
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取会话消息"""
        # TODO: 实现Redis异步数据访问逻辑
        raise NotImplementedError("Redis适配器待实现")
    
    async def get_compressed_contexts(self, session_id: str) -> List[Dict[str, Any]]:
        """获取压缩上下文版本列表"""
        # TODO: 实现Redis异步数据访问逻辑
        raise NotImplementedError("Redis适配器待实现")
    
    async def save_compressed_context(self, session_id: str, compressed_data: Dict[str, Any],
                               version: int, compression_ratio: float,
                               metadata: Dict[str, Any]) -> bool:
        """保存压缩结果"""
        # TODO: 实现Redis异步数据访问逻辑
        raise NotImplementedError("Redis适配器待实现")
    
    async def load_session(self, session_id: str) -> bool:
        """加载会话"""
        # TODO: 实现Redis异步数据访问逻辑
        raise NotImplementedError("Redis适配器待实现")


class MongoDBDataSource(DataSourceInterface):
    """MongoDB数据源（示例实现）"""
    
    def __init__(self, mongodb_client):
        """
        初始化MongoDB适配器
        
        Args:
            mongodb_client: MongoDB客户端实例
        """
        self.mongodb_client = mongodb_client
        self.db = mongodb_client.gtplanner_db
        self.sessions = self.db.sessions
        self.messages = self.db.messages
        self.compressed_contexts = self.db.compressed_contexts
    
    async def get_active_compressed_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取活跃的压缩上下文"""
        # TODO: 实现MongoDB异步数据访问逻辑
        raise NotImplementedError("MongoDB适配器待实现")
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取会话消息"""
        # TODO: 实现MongoDB异步数据访问逻辑
        raise NotImplementedError("MongoDB适配器待实现")
    
    async def get_compressed_contexts(self, session_id: str) -> List[Dict[str, Any]]:
        """获取压缩上下文版本列表"""
        # TODO: 实现MongoDB异步数据访问逻辑
        raise NotImplementedError("MongoDB适配器待实现")
    
    async def save_compressed_context(self, session_id: str, compressed_data: Dict[str, Any],
                               version: int, compression_ratio: float,
                               metadata: Dict[str, Any]) -> bool:
        """保存压缩结果"""
        # TODO: 实现MongoDB异步数据访问逻辑
        raise NotImplementedError("MongoDB适配器待实现")
    
    async def load_session(self, session_id: str) -> bool:
        """加载会话"""
        # TODO: 实现MongoDB异步数据访问逻辑
        raise NotImplementedError("MongoDB适配器待实现")
