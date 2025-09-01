"""
数据库操作层（DAO）

为GTPlanner对话历史持久化系统提供完整的数据库操作接口。
支持CRUD操作、事务管理、会话恢复和对话搜索。
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

from .database_schema import initialize_database


class DatabaseDAO:
    """数据库操作层"""
    
    def __init__(self, db_path: str = "gtplanner_conversations.db"):
        """
        初始化DAO
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_database_initialized()
    
    def _ensure_database_initialized(self):
        """确保数据库已初始化"""
        if not Path(self.db_path).exists():
            print(f"🔧 初始化新数据库: {self.db_path}")
            initialize_database(self.db_path)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    # ==================== 会话管理 ====================
    
    def create_session(self, title: str, project_stage: str = "requirements", 
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题
            project_stage: 项目阶段
            metadata: 元数据
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self.transaction() as conn:
            # 创建会话记录
            conn.execute("""
                INSERT INTO sessions (session_id, title, project_stage, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, title, project_stage, metadata_json))

            # 同时创建初始的compressed_context记录
            context_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO compressed_context (
                    context_id, session_id, compression_version,
                    original_message_count, compressed_message_count,
                    original_token_count, compressed_token_count, compression_ratio,
                    compressed_messages, summary, key_decisions, tool_execution_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context_id, session_id, 1,
                0, 0,  # 初始消息数量为0
                0, 0, 1.0,  # 初始token数量为0，压缩比为1.0
                json.dumps([]), "新会话，暂无内容",
                json.dumps([]), json.dumps({})
            ))

        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息字典或None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "project_stage": row["project_stage"],
                "total_messages": row["total_messages"],
                "total_tokens": row["total_tokens"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "status": row["status"]
            }
    
    def list_sessions(self, limit: int = 50, offset: int = 0,
                     status: str = "active") -> List[Dict[str, Any]]:
        """
        列出会话

        Args:
            limit: 限制数量
            offset: 偏移量
            status: 会话状态

        Returns:
            会话列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM sessions
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "project_stage": row["project_stage"],
                    "total_messages": row["total_messages"],
                    "total_tokens": row["total_tokens"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "status": row["status"]
                })

            return sessions

    def find_sessions_by_partial_id(self, partial_id: str,
                                   status: str = "active") -> List[Dict[str, Any]]:
        """
        根据部分会话ID查找会话

        Args:
            partial_id: 部分会话ID
            status: 会话状态

        Returns:
            匹配的会话列表，按匹配优先级和更新时间排序
        """
        with self.get_connection() as conn:
            # 使用CASE WHEN给前缀匹配更高优先级
            cursor = conn.execute("""
                SELECT *,
                       CASE
                           WHEN session_id LIKE ? THEN 1  -- 前缀匹配优先级高
                           ELSE 2                         -- 包含匹配优先级低
                       END as match_priority
                FROM sessions
                WHERE status = ?
                  AND (session_id LIKE ? OR session_id LIKE ?)
                ORDER BY match_priority ASC, updated_at DESC
            """, (partial_id + '%', status, partial_id + '%', '%' + partial_id + '%'))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "project_stage": row["project_stage"],
                    "total_messages": row["total_messages"],
                    "total_tokens": row["total_tokens"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "status": row["status"],
                    "match_priority": row["match_priority"]
                })

            return sessions
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        更新会话信息
        
        Args:
            session_id: 会话ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        if not kwargs:
            return True
        
        # 构建更新SQL
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ["title", "project_stage", "status"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key == "metadata":
                set_clauses.append("metadata = ?")
                values.append(json.dumps(value) if value else None)
        
        if not set_clauses:
            return True
        
        values.append(session_id)
        sql = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
        
        with self.transaction() as conn:
            cursor = conn.execute(sql, values)
            return cursor.rowcount > 0
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话（软删除）
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                UPDATE sessions SET status = 'deleted' WHERE session_id = ?
            """, (session_id,))
            return cursor.rowcount > 0
    
    # ==================== 消息管理 ====================
    
    def add_message(self, session_id: str, role: str, content: str,
                   metadata: Optional[Dict[str, Any]] = None,
                   tool_calls: Optional[List[Dict[str, Any]]] = None,
                   tool_call_id: Optional[str] = None,
                   parent_message_id: Optional[str] = None,
                   token_count: Optional[int] = None) -> str:
        """
        添加消息（支持OpenAI API标准格式）

        Args:
            session_id: 会话ID
            role: 角色（user, assistant, system, tool）
            content: 消息内容
            metadata: 元数据
            tool_calls: 工具调用信息（assistant消息专用）
            tool_call_id: 工具调用ID（tool消息专用）
            parent_message_id: 父消息ID
            token_count: token数量

        Returns:
            消息ID
        """
        message_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None

        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO messages (
                    message_id, session_id, role, content, token_count,
                    metadata, tool_calls, tool_call_id, parent_message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (message_id, session_id, role, content, token_count,
                  metadata_json, tool_calls_json, tool_call_id, parent_message_id))

            # 更新会话的token计数
            if token_count:
                conn.execute("""
                    UPDATE sessions
                    SET total_tokens = total_tokens + ?
                    WHERE session_id = ?
                """, (token_count, session_id))

        return message_id
    
    def get_messages(self, session_id: str, limit: Optional[int] = None,
                    role_filter: Optional[str] = None,
                    include_compressed: bool = True) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        Args:
            session_id: 会话ID
            limit: 限制数量
            role_filter: 角色过滤
            include_compressed: 是否包含压缩消息
            
        Returns:
            消息列表
        """
        sql = "SELECT * FROM messages WHERE session_id = ?"
        params = [session_id]
        
        if role_filter:
            sql += " AND role = ?"
            params.append(role_filter)
        
        if not include_compressed:
            sql += " AND is_compressed = FALSE"
        
        sql += " ORDER BY timestamp ASC"
        
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "message_id": row["message_id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "token_count": row["token_count"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else [],
                    "parent_message_id": row["parent_message_id"]
                })
            
            return messages
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            session_id: 会话ID
            count: 消息数量
            
        Returns:
            最近的消息列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, count))

            messages = []
            for row in reversed(cursor.fetchall()):  # 反转以保持时间顺序
                messages.append({
                    "message_id": row["message_id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "token_count": row["token_count"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else [],
                    "parent_message_id": row["parent_message_id"]
                })
            
            return messages

    # ==================== 压缩上下文管理 ====================

    def create_compressed_context(self, session_id: str,
                                 original_message_count: int,
                                 compressed_messages: List[Dict[str, Any]],
                                 summary: str,
                                 key_decisions: Optional[List[Dict[str, Any]]] = None,
                                 tool_execution_results: Optional[Dict[str, Any]] = None) -> str:
        """
        创建压缩上下文

        Args:
            session_id: 会话ID
            original_message_count: 原始消息数量
            compressed_messages: 压缩后的消息列表
            summary: 对话摘要
            key_decisions: 关键决策
            tool_execution_results: 工具执行结果集合

        Returns:
            压缩上下文ID
        """
        context_id = str(uuid.uuid4())

        # 计算压缩统计
        compressed_message_count = len(compressed_messages)
        original_token_count = sum(msg.get("token_count", 0) for msg in compressed_messages)
        compressed_token_count = len(summary.split())  # 简单估算
        compression_ratio = compressed_token_count / max(original_token_count, 1)

        # 获取当前压缩版本
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COALESCE(MAX(compression_version), 0) + 1 as next_version
                FROM compressed_context WHERE session_id = ?
            """, (session_id,))
            compression_version = cursor.fetchone()[0]

        compressed_messages_json = json.dumps(compressed_messages)
        key_decisions_json = json.dumps(key_decisions) if key_decisions else None
        tool_execution_results_json = json.dumps(tool_execution_results) if tool_execution_results else None

        with self.transaction() as conn:
            # 将之前的压缩上下文设为非活跃
            conn.execute("""
                UPDATE compressed_context
                SET is_active = FALSE
                WHERE session_id = ? AND is_active = TRUE
            """, (session_id,))

            # 插入新的压缩上下文
            conn.execute("""
                INSERT INTO compressed_context (
                    context_id, session_id, compression_version,
                    original_message_count, compressed_message_count,
                    original_token_count, compressed_token_count, compression_ratio,
                    compressed_messages, summary, key_decisions, tool_execution_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (context_id, session_id, compression_version,
                  original_message_count, compressed_message_count,
                  original_token_count, compressed_token_count, compression_ratio,
                  compressed_messages_json, summary, key_decisions_json, tool_execution_results_json))

            # 更新会话的压缩状态
            conn.execute("""
                UPDATE sessions
                SET is_compressed = TRUE, last_compression_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))

        return context_id

    def get_active_compressed_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取活跃的压缩上下文

        Args:
            session_id: 会话ID

        Returns:
            压缩上下文信息或None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM compressed_context
                WHERE session_id = ? AND is_active = TRUE
                ORDER BY compression_version DESC
                LIMIT 1
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "context_id": row["context_id"],
                "session_id": row["session_id"],
                "compression_version": row["compression_version"],
                "created_at": row["created_at"],
                "original_message_count": row["original_message_count"],
                "compressed_message_count": row["compressed_message_count"],
                "original_token_count": row["original_token_count"],
                "compressed_token_count": row["compressed_token_count"],
                "compression_ratio": row["compression_ratio"],
                "compressed_messages": json.loads(row["compressed_messages"]),
                "summary": row["summary"],
                "key_decisions": json.loads(row["key_decisions"]) if row["key_decisions"] else [],
                "tool_execution_results": json.loads(row["tool_execution_results"]) if row["tool_execution_results"] else {},
                "is_active": bool(row["is_active"])
            }

    def get_compressed_contexts(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的所有压缩上下文

        Args:
            session_id: 会话ID

        Returns:
            压缩上下文列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM compressed_context
                WHERE session_id = ?
                ORDER BY compression_version DESC
            """, (session_id,))

            contexts = []
            for row in cursor.fetchall():
                contexts.append({
                    "context_id": row["context_id"],
                    "session_id": row["session_id"],
                    "version": row["compression_version"],
                    "created_at": row["created_at"],
                    "original_message_count": row["original_message_count"],
                    "compressed_message_count": row["compressed_message_count"],
                    "original_token_count": row["original_token_count"],
                    "compressed_token_count": row["compressed_token_count"],
                    "compression_ratio": row["compression_ratio"],
                    "compressed_data": {
                        "messages": json.loads(row["compressed_messages"]),
                        "summary": row["summary"],
                        "key_decisions": json.loads(row["key_decisions"]) if row["key_decisions"] else []
                    },
                    "tool_execution_results": json.loads(row["tool_execution_results"]) if row["tool_execution_results"] else {},
                    "is_active": bool(row["is_active"])
                })

            return contexts

    def save_compressed_context(self, session_id: str, compressed_data: Dict[str, Any],
                               version: int, compression_ratio: float,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        保存压缩上下文（新的简化接口）

        Args:
            session_id: 会话ID
            compressed_data: 压缩数据
            version: 版本号
            compression_ratio: 压缩比
            metadata: 元数据

        Returns:
            压缩上下文ID
        """
        context_id = str(uuid.uuid4())

        # 从压缩数据中提取信息
        messages = compressed_data.get('messages', [])
        summary = compressed_data.get('summary', '')
        key_decisions = compressed_data.get('key_decisions', [])

        original_count = compressed_data.get('original_count', 0)
        compressed_count = len(messages)

        with self.transaction() as conn:
            # 将之前的压缩上下文设为非活跃
            conn.execute("""
                UPDATE compressed_context
                SET is_active = FALSE
                WHERE session_id = ? AND is_active = TRUE
            """, (session_id,))

            # 插入新的压缩上下文
            conn.execute("""
                INSERT INTO compressed_context (
                    context_id, session_id, compression_version,
                    original_message_count, compressed_message_count,
                    original_token_count, compressed_token_count, compression_ratio,
                    compressed_messages, summary, key_decisions, tool_execution_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context_id, session_id, version,
                original_count, compressed_count,
                0, 0, compression_ratio,  # token counts暂时设为0
                json.dumps(messages), summary, json.dumps(key_decisions),
                json.dumps(metadata) if metadata else None
            ))

        return context_id

    def delete_compressed_context(self, session_id: str, version: int) -> bool:
        """
        删除指定版本的压缩上下文

        Args:
            session_id: 会话ID
            version: 版本号

        Returns:
            是否删除成功
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                DELETE FROM compressed_context
                WHERE session_id = ? AND compression_version = ?
            """, (session_id, version))

            return cursor.rowcount > 0

    def get_compressed_context_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        从compressed_context表获取消息（Agent层的唯一数据源）

        Args:
            session_id: 会话ID

        Returns:
            压缩上下文中的消息列表

        Raises:
            ValueError: 如果找不到压缩上下文记录（数据不一致）
        """
        # 获取活跃的压缩上下文
        compressed_context = self.get_active_compressed_context(session_id)

        if not compressed_context:
            # 这是异常情况，说明数据不一致
            print(f"⚠️ 警告：会话 {session_id} 缺少压缩上下文记录，数据可能不一致")
            raise ValueError(f"会话 {session_id} 缺少压缩上下文记录，请检查会话创建流程")

        # 直接从压缩上下文中解析消息
        return compressed_context.get("compressed_messages", [])



    # ==================== 工具执行管理 ====================





    # ==================== 搜索功能 ====================

    def search_sessions_by_keyword(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        按关键词搜索会话

        Args:
            keyword: 关键词
            limit: 结果限制

        Returns:
            匹配的会话列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT s.*
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.session_id
                WHERE s.title LIKE ? OR m.content LIKE ?
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "project_stage": row["project_stage"],
                    "total_messages": row["total_messages"],
                    "total_tokens": row["total_tokens"],
                    "is_compressed": bool(row["is_compressed"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "status": row["status"]
                })

            return sessions

    # ==================== 统计功能 ====================

    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        with self.get_connection() as conn:
            # 基本统计
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_messages,
                    SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
                    SUM(COALESCE(token_count, 0)) as total_tokens,
                    MIN(timestamp) as first_message_at,
                    MAX(timestamp) as last_message_at
                FROM messages
                WHERE session_id = ?
            """, (session_id,))

            stats = dict(cursor.fetchone())

            # 简化统计：只保留基本的消息统计

            return stats

    def get_global_statistics(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            全局统计信息字典
        """
        with self.get_connection() as conn:
            stats = {}

            # 会话统计
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_sessions,
                    SUM(total_messages) as total_messages,
                    SUM(total_tokens) as total_tokens,
                    AVG(total_messages) as avg_messages_per_session
                FROM sessions
            """)
            stats.update(dict(cursor.fetchone()))

            # 简化统计：删除复杂的工具统计

            return stats
