"""
基于SQLite的会话和消息管理系统

完全替换现有的文件存储方式，使用SQLite数据库进行高效的会话和消息管理。
支持与StatelessGTPlanner的AgentContext转换，兼容流式响应系统。
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .database_dao import DatabaseDAO
from ..context_types import AgentContext, Message, MessageRole


class SQLiteSessionManager:
    """基于SQLite的会话管理器"""
    
    def __init__(self, db_path: str = "gtplanner_conversations.db"):
        """
        初始化SQLite会话管理器

        Args:
            db_path: 数据库文件路径
        """
        self.dao = DatabaseDAO(db_path)
        self.current_session_id: Optional[str] = None
        self._compressor = None  # 延迟初始化压缩器
        self._session_cache = {}  # 会话缓存

    @property
    def compressor(self):
        """获取压缩器实例（延迟初始化）"""
        if self._compressor is None:
            from .smart_compressor import SmartCompressor
            self._compressor = SmartCompressor(self)
        return self._compressor
    
    # ==================== 会话管理 ====================
    
    def create_new_session(self, title: Optional[str] = None, 
                          project_stage: str = "requirements") -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题，如果为None则自动生成
            project_stage: 项目阶段
            
        Returns:
            新会话的ID
        """
        if not title:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            title = f"新会话 - {timestamp}"
        
        # 创建会话
        session_id = self.dao.create_session(
            title=title,
            project_stage=project_stage,
            metadata={
                "created_by": "sqlite_session_manager",
                "version": "1.0"
            }
        )
        
        # 设置为当前会话
        self.current_session_id = session_id
        
        # 清除缓存
        self._session_cache.clear()
        
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """
        加载指定会话

        Args:
            session_id: 会话ID

        Returns:
            是否加载成功
        """
        session = self.dao.get_session(session_id)
        if session and session["status"] == "active":
            self.current_session_id = session_id
            # 清除缓存以强制重新加载
            self._session_cache.clear()
            return True
        return False

    def find_sessions_by_partial_id(self, partial_id: str) -> List[Dict[str, Any]]:
        """
        根据部分会话ID查找会话

        Args:
            partial_id: 部分会话ID

        Returns:
            匹配的会话列表
        """
        return self.dao.find_sessions_by_partial_id(partial_id)

    def load_session_by_partial_id(self, partial_id: str) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        根据部分会话ID加载会话

        Args:
            partial_id: 部分会话ID

        Returns:
            (是否成功, 加载的会话ID, 匹配的会话列表)
        """
        # 首先尝试精确匹配（向后兼容）
        if self.load_session(partial_id):
            return True, partial_id, []

        # 精确匹配失败，尝试模糊匹配
        matches = self.find_sessions_by_partial_id(partial_id)

        if not matches:
            return False, None, []
        elif len(matches) == 1:
            # 只有一个匹配，直接加载
            session_id = matches[0]["session_id"]
            success = self.load_session(session_id)
            return success, session_id if success else None, matches
        else:
            # 多个匹配，返回列表供用户选择
            return False, None, matches
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        获取当前会话信息
        
        Returns:
            当前会话信息或None
        """
        if not self.current_session_id:
            return None
        
        # 使用缓存
        if self.current_session_id in self._session_cache:
            return self._session_cache[self.current_session_id]
        
        session = self.dao.get_session(self.current_session_id)
        if session:
            self._session_cache[self.current_session_id] = session
        
        return session
    
    def list_sessions(self, limit: int = 50, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        列出会话
        
        Args:
            limit: 限制数量
            include_archived: 是否包含已归档的会话
            
        Returns:
            会话列表
        """
        if include_archived:
            # 获取活跃和已归档的会话
            active_sessions = self.dao.list_sessions(limit=limit//2, status="active")
            archived_sessions = self.dao.list_sessions(limit=limit//2, status="archived")
            return active_sessions + archived_sessions
        else:
            return self.dao.list_sessions(limit=limit, status="active")
    
    def update_session_title(self, title: str, session_id: Optional[str] = None) -> bool:
        """
        更新会话标题
        
        Args:
            title: 新标题
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, title=title)
        if success and target_session_id in self._session_cache:
            # 更新缓存
            self._session_cache[target_session_id]["title"] = title
        
        return success
    
    def update_project_stage(self, stage: str, session_id: Optional[str] = None) -> bool:
        """
        更新项目阶段
        
        Args:
            stage: 新的项目阶段
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, project_stage=stage)
        if success and target_session_id in self._session_cache:
            # 更新缓存
            self._session_cache[target_session_id]["project_stage"] = stage
        
        return success
    
    def archive_session(self, session_id: Optional[str] = None) -> bool:
        """
        归档会话
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否归档成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.update_session(target_session_id, status="archived")
        if success:
            # 如果归档的是当前会话，清除当前会话
            if target_session_id == self.current_session_id:
                self.current_session_id = None
            
            # 清除缓存
            if target_session_id in self._session_cache:
                del self._session_cache[target_session_id]
        
        return success
    
    def delete_session(self, session_id: Optional[str] = None) -> bool:
        """
        删除会话（软删除）
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            是否删除成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False
        
        success = self.dao.delete_session(target_session_id)
        if success:
            # 如果删除的是当前会话，清除当前会话
            if target_session_id == self.current_session_id:
                self.current_session_id = None
            
            # 清除缓存
            if target_session_id in self._session_cache:
                del self._session_cache[target_session_id]
        
        return success
    
    # ==================== 消息管理 ====================
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None,
                        session_id: Optional[str] = None) -> Optional[str]:
        """
        添加用户消息
        
        Args:
            content: 消息内容
            metadata: 消息元数据
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None
        
        # 估算token数量（改进的估算方法）
        # 中文字符按1个token计算，英文单词按1个token计算，标点符号等按0.5计算
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_words = len(content.replace('，', ' ').replace('。', ' ').split())
        other_chars = len(content) - chinese_chars - sum(len(word) for word in content.split())
        token_count = chinese_chars + english_words + max(1, other_chars // 2)
        
        # 同时写入messages表和compressed_context表
        message_id = self.dao.add_message(
            session_id=target_session_id,
            role="user",
            content=content,
            metadata=metadata,
            token_count=int(token_count)
        )

        if message_id:
            # 更新compressed_context表
            self._update_compressed_context_with_new_message(
                target_session_id, message_id, "user", content,
                int(token_count), metadata
            )

        # 清除会话缓存以更新统计信息
        if target_session_id in self._session_cache:
            del self._session_cache[target_session_id]

        return message_id

    def add_tool_message(self, content: str, tool_call_id: str,
                        metadata: Optional[Dict[str, Any]] = None,
                        parent_message_id: Optional[str] = None,
                        session_id: Optional[str] = None) -> Optional[str]:
        """
        添加工具消息（OpenAI API标准格式）

        Args:
            content: 工具执行结果内容（JSON字符串）
            tool_call_id: 工具调用ID（关联assistant消息中的tool_calls）
            metadata: 消息元数据
            parent_message_id: 父消息ID
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            消息ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        # 估算token数量（工具结果通常是JSON格式）
        token_count = max(1, len(content) // 4)  # 简单估算

        # 保存到messages表
        message_id = self.dao.add_message(
            session_id=target_session_id,
            role="tool",
            content=content,
            metadata=metadata,
            tool_call_id=tool_call_id,
            parent_message_id=parent_message_id,
            token_count=int(token_count)
        )

        if message_id:
            # 更新compressed_context表
            self._update_compressed_context_with_new_message(
                target_session_id, message_id, "tool", content,
                int(token_count), metadata, tool_call_id=tool_call_id
            )

        # 清除会话缓存以更新统计信息
        if target_session_id in self._session_cache:
            del self._session_cache[target_session_id]

        return message_id

    def add_assistant_message(self, content: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            tool_calls: Optional[List[Dict[str, Any]]] = None,
                            parent_message_id: Optional[str] = None,
                            session_id: Optional[str] = None) -> Optional[str]:
        """
        添加助手消息
        
        Args:
            content: 消息内容
            metadata: 消息元数据
            tool_calls: 工具调用信息
            parent_message_id: 父消息ID
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息ID或None（如果失败）
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None
        
        # 估算token数量（改进的估算方法）
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_words = len(content.replace('，', ' ').replace('。', ' ').split())
        other_chars = len(content) - chinese_chars - sum(len(word) for word in content.split())
        token_count = chinese_chars + english_words + max(1, other_chars // 2)
        
        # 同时写入messages表和compressed_context表
        message_id = self.dao.add_message(
            session_id=target_session_id,
            role="assistant",
            content=content,
            metadata=metadata,
            tool_calls=tool_calls,
            parent_message_id=parent_message_id,
            token_count=int(token_count)
        )

        if message_id:
            # 更新compressed_context表
            self._update_compressed_context_with_new_message(
                target_session_id, message_id, "assistant", content,
                int(token_count), metadata, tool_calls
            )

        # 清除会话缓存以更新统计信息
        if target_session_id in self._session_cache:
            del self._session_cache[target_session_id]

        return message_id

    def _update_compressed_context_with_new_message(self, session_id: str, message_id: str,
                                                   role: str, content: str, token_count: int,
                                                   metadata: Optional[Dict[str, Any]] = None,
                                                   tool_calls: Optional[List[Dict[str, Any]]] = None,
                                                   tool_call_id: Optional[str] = None):
        """
        更新compressed_context表，添加新消息

        Args:
            session_id: 会话ID
            message_id: 消息ID
            role: 消息角色
            content: 消息内容
            token_count: token数量
            metadata: 元数据
            tool_calls: 工具调用
        """
        # 获取当前活跃的压缩上下文
        current_context = self.dao.get_active_compressed_context(session_id)

        # 构建新消息对象（OpenAI API标准格式）
        new_message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "token_count": token_count,
            "metadata": metadata or {}
        }

        # 根据消息类型添加特定字段
        if role == "assistant" and tool_calls:
            new_message["tool_calls"] = tool_calls
        elif role == "tool" and tool_call_id:
            new_message["tool_call_id"] = tool_call_id

        if current_context:
            # 更新现有压缩上下文
            compressed_messages = current_context.get("compressed_messages", [])
            compressed_messages.append(new_message)

            # 更新统计信息
            new_compressed_token_count = current_context["compressed_token_count"] + token_count
            new_compressed_message_count = current_context["compressed_message_count"] + 1
            new_original_token_count = current_context["original_token_count"] + token_count
            new_original_message_count = current_context["original_message_count"] + 1

            # 更新数据库记录
            with self.dao.transaction() as conn:
                conn.execute("""
                    UPDATE compressed_context
                    SET compressed_messages = ?,
                        compressed_message_count = ?,
                        compressed_token_count = ?,
                        original_message_count = ?,
                        original_token_count = ?
                    WHERE context_id = ?
                """, (
                    json.dumps(compressed_messages),
                    new_compressed_message_count,
                    new_compressed_token_count,
                    new_original_message_count,
                    new_original_token_count,
                    current_context["context_id"]
                ))
        else:
            # 这是异常情况，压缩上下文应该在会话创建时就存在
            print(f"⚠️ 警告：会话 {session_id} 缺少压缩上下文记录")
            raise ValueError(f"会话 {session_id} 缺少压缩上下文记录，请检查会话创建流程")

    def _update_compressed_context_tool_results(self, session_id: str,
                                              tool_execution_updates: Dict[str, Any]):
        """
        更新compressed_context表中的工具执行结果

        Args:
            session_id: 会话ID
            tool_execution_updates: 工具执行结果更新（recommended_tools, short_planning等）
        """

        current_context = self.dao.get_active_compressed_context(session_id)
        if not current_context:
            print(f"⚠️ 警告：会话 {session_id} 缺少压缩上下文记录")
            return

        # 合并工具执行结果更新
        current_tool_results = current_context.get("tool_execution_results", {})

        if isinstance(current_tool_results, str):
            current_tool_results = json.loads(current_tool_results) if current_tool_results else {}

        # 更新工具执行结果
        current_tool_results.update(tool_execution_updates)


        # 更新数据库记录
        with self.dao.transaction() as conn:
            conn.execute("""
                UPDATE compressed_context
                SET tool_execution_results = ?
                WHERE context_id = ?
            """, (
                json.dumps(current_tool_results),
                current_context["context_id"]
            ))

    def get_messages(self, limit: Optional[int] = None,
                    session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        Args:
            limit: 限制数量
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            消息列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []
        
        return self.dao.get_messages(target_session_id, limit=limit)
    
    def get_recent_messages(self, count: int = 10, 
                          session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            最近的消息列表
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return []
        
        return self.dao.get_recent_messages(target_session_id, count=count)

    # ==================== 工具执行管理已删除 ====================
    # 注意：工具执行信息现在通过OpenAI标准格式的tool消息保存
    # 使用add_tool_message()和相关消息方法即可

    # ==================== AgentContext转换 ====================

    def build_agent_context(self, session_id: Optional[str] = None,
                           include_recent_only: bool = False,
                           recent_count: int = 20) -> Optional[AgentContext]:
        """
        构建AgentContext对象

        Args:
            session_id: 会话ID，如果为None则使用当前会话
            include_recent_only: 是否只包含最近的消息
            recent_count: 最近消息的数量

        Returns:
            AgentContext对象或None
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        # 获取会话信息
        session = self.dao.get_session(target_session_id)
        if not session:
            return None

        # 获取消息
        if include_recent_only:
            message_data = self.dao.get_recent_messages(target_session_id, count=recent_count)
        else:
            message_data = self.dao.get_messages(target_session_id)

        # 转换消息格式
        dialogue_history = []
        for msg_data in message_data:
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data["metadata"],
                tool_calls=msg_data.get("tool_calls"),
                tool_call_id=msg_data.get("tool_call_id")
            )
            dialogue_history.append(message)


        # 构建工具执行结果（从会话元数据中获取）
        tool_execution_results = session["metadata"].get("tool_execution_results", {})

        # 构建AgentContext
        context = AgentContext(
            session_id=target_session_id,
            dialogue_history=dialogue_history,
            tool_execution_results=tool_execution_results,
            # tool_execution_history已删除
            session_metadata=session["metadata"]
        )

        return context

    def update_from_agent_result(self, agent_result, user_input: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        """
        从AgentResult更新会话数据

        Args:
            agent_result: StatelessGTPlanner的处理结果
            user_input: 用户输入（如果提供，会先保存用户消息）
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            是否更新成功
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False

        try:
            # 如果提供了用户输入，先保存用户消息
            if user_input:
                self.add_user_message(
                    content=user_input,
                    session_id=target_session_id
                )

            # 保存新的消息（支持OpenAI API标准格式）
            for message in agent_result.new_messages:
                if message.role.value == "assistant":
                    self.add_assistant_message(
                        content=message.content,
                        metadata=message.metadata,
                        tool_calls=message.tool_calls if message.tool_calls else None,
                        session_id=target_session_id
                    )
                elif message.role.value == "tool":
                    # 确保tool_call_id不为空，否则跳过这条消息
                    if message.tool_call_id and message.tool_call_id.strip():
                        self.add_tool_message(
                            content=message.content,
                            tool_call_id=message.tool_call_id,
                            metadata=message.metadata,
                            session_id=target_session_id
                        )
                    else:
                        print(f"⚠️ 跳过无效的tool消息：tool_call_id为空")
                elif message.role.value == "user":
                    self.add_user_message(
                        content=message.content,
                        metadata=message.metadata,
                        session_id=target_session_id
                    )

            # 更新工具执行结果到compressed_context表（如果有变化）
            if hasattr(agent_result, 'tool_execution_results_updates') and agent_result.tool_execution_results_updates:
                self._update_compressed_context_tool_results(
                    target_session_id, agent_result.tool_execution_results_updates
                )
            return True

        except Exception as e:
            print(f"更新会话数据失败: {e}")
            return False

    # ==================== 搜索和统计 ====================

    def search_sessions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索会话

        Args:
            keyword: 搜索关键词
            limit: 结果限制

        Returns:
            匹配的会话列表
        """
        return self.dao.search_sessions_by_keyword(keyword, limit=limit)

    def get_session_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            统计信息字典
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return {}

        return self.dao.get_session_statistics(target_session_id)

    def get_global_statistics(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            全局统计信息字典
        """
        return self.dao.get_global_statistics()



    # ==================== AgentContext转换 ====================

    def build_agent_context(self, session_id: Optional[str] = None) -> Optional[AgentContext]:
        """
        构建AgentContext对象（从compressed_context表读取数据）

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            AgentContext对象或None
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return None

        # 获取会话信息
        session = self.dao.get_session(target_session_id)
        if not session:
            return None

        # 从compressed_context表获取消息（Agent层的唯一数据源）
        message_data = self.dao.get_compressed_context_messages(target_session_id)

        # 获取活跃的压缩上下文（包含项目状态等信息）
        compressed_context = self.dao.get_active_compressed_context(target_session_id)
        if not compressed_context:
            print(f"⚠️ 警告：会话 {target_session_id} 缺少压缩上下文记录")
            return None

        # 转换消息格式
        dialogue_history = []
        for msg_data in message_data:
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data["metadata"],
                tool_calls=msg_data.get("tool_calls"),
                tool_call_id=msg_data.get("tool_call_id")
            )
            dialogue_history.append(message)

        # 工具执行历史已删除 - 过度设计，不再需要

        # 从compressed_context表获取工具执行结果
        tool_execution_results = compressed_context.get("tool_execution_results", {})
        if isinstance(tool_execution_results, str):
            tool_execution_results = json.loads(tool_execution_results) if tool_execution_results else {}

        # 构建AgentContext（完全基于compressed_context表的数据）
        context = AgentContext(
            session_id=target_session_id,
            dialogue_history=dialogue_history,
            tool_execution_results=tool_execution_results,
            session_metadata=session["metadata"],  # 基本元数据从session表获取
            is_compressed=compressed_context["compression_version"] > 1  # 标识是否已压缩
        )

        return context

    # 重复的update_from_agent_result方法已删除

    # ==================== 搜索和统计 ====================

    def search_sessions(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索会话

        Args:
            keyword: 搜索关键词
            limit: 结果限制

        Returns:
            匹配的会话列表
        """
        return self.dao.search_sessions_by_keyword(keyword, limit=limit)

    def get_session_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            统计信息字典
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return {}

        return self.dao.get_session_statistics(target_session_id)

    def get_global_statistics(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            全局统计信息字典
        """
        return self.dao.get_global_statistics()


