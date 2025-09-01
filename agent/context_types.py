"""
GTPlanner Agent层无状态化数据结构定义

定义了Agent层无状态重构所需的核心数据类型：
- AgentContext: 客户端传入的完整上下文信息（只读）
- AgentResult: Agent处理结果，只包含当次对话新增的内容
- Message: 标准化的对话消息
- ToolExecution: 标准化的工具执行记录

设计原则：
1. Agent层完全无状态：不维护任何状态，不修改传入的上下文
2. 纯函数式处理：相同输入产生相同输出
3. 增量返回：只返回当次对话新增的内容，项目状态采用全量更新保证一致性
4. 客户端负责状态管理：所有状态的持久化和更新由客户端处理
5. 支持压缩上下文：客户端可以压缩历史上下文以控制token使用量

所有数据类都支持序列化/反序列化，确保在客户端和Agent层之间的数据传递。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"





@dataclass
class Message:
    """标准化的对话消息数据结构（完全符合OpenAI API标准格式）"""
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None  # assistant消息专用
    tool_call_id: Optional[str] = None  # tool消息专用

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（OpenAI API标准格式）"""
        result = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }

        # 根据消息类型添加特定字段
        if self.role == MessageRole.ASSISTANT and self.tool_calls:
            result["tool_calls"] = self.tool_calls
        elif self.role == MessageRole.TOOL and self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建Message实例"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id")
        )


# ToolExecution类已删除 - 过度设计，工具执行信息现在通过OpenAI标准格式的tool消息保存


@dataclass
class AgentContext:
    """Agent上下文数据结构 - 客户端传入的上下文信息（可能已压缩）"""
    session_id: str
    dialogue_history: List[Message]  # 可能是压缩后的对话历史
    tool_execution_results: Dict[str, Any]  # 工具执行结果集合（recommended_tools, short_planning, research_findings等）
    session_metadata: Dict[str, Any]
    last_updated: Optional[str] = None
    is_compressed: bool = False  # 标识上下文是否已被压缩
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "dialogue_history": [msg.to_dict() for msg in self.dialogue_history],
            "tool_execution_results": self.tool_execution_results,
            "session_metadata": self.session_metadata,
            "last_updated": self.last_updated,
            "is_compressed": self.is_compressed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """从字典创建AgentContext实例"""
        return cls(
            session_id=data["session_id"],
            dialogue_history=[
                Message.from_dict(msg_data)
                for msg_data in data.get("dialogue_history", [])
            ],
            tool_execution_results=data.get("tool_execution_results", {}),
            # tool_execution_history已删除
            session_metadata=data.get("session_metadata", {}),
            last_updated=data.get("last_updated"),
            is_compressed=data.get("is_compressed", False)
        )
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """获取最近的消息（只读操作）"""
        return self.dialogue_history[-count:] if self.dialogue_history else []

    def get_tool_execution_result(self, key: str, default: Any = None) -> Any:
        """获取工具执行结果值（只读操作）"""
        return self.tool_execution_results.get(key, default)

    # get_recent_tool_executions方法已删除 - 过度设计，不再需要


@dataclass
class AgentResult:
    """Agent处理结果数据结构 - 只包含当次对话新增的内容（OpenAI API标准格式）"""
    success: bool
    new_messages: List[Message]  # 当次对话新增的所有消息（assistant、tool等，按时间顺序）
    tool_execution_results_updates: Dict[str, Any] = field(default_factory=dict)  # 当次对话产生的工具执行结果更新（pocketflow内部传递）
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "new_messages": [msg.to_dict() for msg in self.new_messages],
            "tool_execution_results_updates": self.tool_execution_results_updates,
            "metadata": self.metadata,
            "error": self.error,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResult':
        """从字典创建AgentResult实例"""
        return cls(
            success=data["success"],
            new_messages=[
                Message.from_dict(msg_data)
                for msg_data in data.get("new_messages", [])
            ],
            tool_execution_results_updates=data.get("tool_execution_results_updates", {}),
            metadata=data.get("metadata", {}),
            error=data.get("error"),
            execution_time=data.get("execution_time")
        )
    
    @classmethod
    def create_success(
        cls,
        new_messages: Optional[List[Message]] = None,
        tool_execution_results_updates: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> 'AgentResult':
        """创建成功结果"""
        return cls(
            success=True,
            new_messages=new_messages or [],
            tool_execution_results_updates=tool_execution_results_updates or {},
            metadata=metadata or {},
            execution_time=execution_time
        )
    
    @classmethod
    def create_error(
        cls,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> 'AgentResult':
        """创建错误结果"""
        return cls(
            success=False,
            new_messages=[],
            tool_execution_results_updates={},
            metadata=metadata or {},
            error=error,
            execution_time=execution_time
        )


# 工具函数：用于数据验证和转换



def create_user_message(content: str) -> Message:
    """创建用户消息的便捷函数"""
    return Message(
        role=MessageRole.USER,
        content=content,
        timestamp=datetime.now().isoformat()
    )


def create_assistant_message(
    content: str,
    tool_calls: Optional[List[Dict[str, Any]]] = None
) -> Message:
    """创建助手消息的便捷函数"""
    return Message(
        role=MessageRole.ASSISTANT,
        content=content,
        timestamp=datetime.now().isoformat(),
        tool_calls=tool_calls
    )


def create_tool_message(
    content: str,
    tool_call_id: str
) -> Message:
    """创建工具消息的便捷函数（OpenAI API标准格式）"""
    return Message(
        role=MessageRole.TOOL,
        content=content,
        timestamp=datetime.now().isoformat(),
        tool_call_id=tool_call_id
    )