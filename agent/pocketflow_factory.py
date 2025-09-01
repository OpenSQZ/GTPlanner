"""
PocketFlow工厂 - 无状态版本

负责从AgentContext创建pocketflow shared字典，以及从shared字典中提取AgentResult。
实现上下文数据和pocketflow格式之间的转换。

设计原则：
1. 纯静态方法：所有方法都是静态的，不维护任何状态
2. 单向转换：只负责数据格式转换，不修改原始数据
3. 简洁实用：专注核心功能，避免过度设计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .context_types import (
    AgentContext, AgentResult, Message,
    MessageRole
)


class PocketFlowSharedFactory:
    """PocketFlow Shared字典工厂 - 纯静态方法"""
    
    @staticmethod
    def create_shared_dict(
        user_input: str,
        context: AgentContext,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从用户输入和AgentContext创建pocketflow shared字典

        Args:
            user_input: 当前用户输入
            context: Agent上下文（只读，可能已压缩）
            language: 语言选择，支持 'zh', 'en', 'ja', 'es', 'fr'（可选）

        Returns:
            pocketflow shared字典

        Raises:
            ValueError: 当上下文数据无效时
        """
        # 验证上下文数据
        PocketFlowSharedFactory._validate_context(context)
        # 构建对话历史（包含当前用户输入）
        # 注意：context.dialogue_history 可能已经被客户端压缩
        current_messages = []

        # 添加历史消息（可能是压缩后的）
        for msg in context.dialogue_history:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content
            }

            # 添加OpenAI API标准字段
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id

            current_messages.append(message_dict)

        # 添加当前用户输入
        current_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 构建基础shared字典
        shared = {
            # 核心对话数据
            "dialogue_history": {"messages": current_messages},
            "session_id": context.session_id,

            # 语言选择 - 添加到shared字典中供各个节点使用
            "language": language,

            # 工具执行结果数据（统一字段名）- 只设置非空值，避免覆盖工具执行结果
            # 注意：工具节点会在执行后设置这些字段，这里只设置已有的非空值
        }

        # 只设置已存在且非空的工具执行结果
        for key in ["recommended_tools", "research_findings", "short_planning"]:
            value = context.tool_execution_results.get(key)
            if value is not None:
                shared[key] = value

        # 继续添加其他字段
        shared.update({
            # 工具执行历史已删除 - 过度设计，不再需要

            # 流程控制数据
            "flow_start_time": None,  # 将在prep_async中设置
            "flow_metadata": {},
            "react_error": None,
            "react_post_error": None,

            # 会话元数据
            "session_metadata": context.session_metadata.copy(),
            "last_updated": context.last_updated,

            # Agent执行过程中新增的内容（初始化为空）
            "new_messages": [],  # 新增的所有消息（assistant、tool等，OpenAI API标准格式）
        })
        
        return shared
    
    @staticmethod
    def create_agent_result(
        shared: Dict[str, Any],
        execution_time: Optional[float] = None
    ) -> AgentResult:
        """
        从执行后的shared字典创建AgentResult

        Args:
            shared: 执行后的shared字典
            execution_time: 执行时间

        Returns:
            AgentResult对象
        """
        try:
            # 检查是否有错误
            error = shared.get("react_error") or shared.get("react_post_error")

            if error:
                return AgentResult.create_error(
                    error=str(error),
                    metadata=shared.get("flow_metadata", {}),
                    execution_time=execution_time
                )

            # 直接从预留字段获取新增内容（OpenAI API标准格式）
            new_messages = PocketFlowSharedFactory._parse_new_messages(
                shared.get("new_messages", [])
            )

            # 提取工具执行结果更新 - 从shared字典中提取工具执行结果
            tool_execution_results_updates = {}

            # 检查各个工具的执行结果（统一字段名）
            if "recommended_tools" in shared:
                tool_execution_results_updates["recommended_tools"] = shared["recommended_tools"]

            if "research_findings" in shared:
                tool_execution_results_updates["research_findings"] = shared["research_findings"]

            if "short_planning" in shared:
                tool_execution_results_updates["short_planning"] = shared["short_planning"]

            # 检查设计文档相关字段 - 组织在 designs 命名空间下
            designs = {}

            # 深度设计文档字段
            if "analysis_markdown" in shared:
                designs["analysis_markdown"] = shared["analysis_markdown"]

            if "nodes_markdown" in shared:
                designs["nodes_markdown"] = shared["nodes_markdown"]

            if "flow_markdown" in shared:
                designs["flow_markdown"] = shared["flow_markdown"]

            if "data_structure_json" in shared:
                designs["data_structure_json"] = shared["data_structure_json"]

            if "node_design_markdown" in shared:
                designs["node_design_markdown"] = shared["node_design_markdown"]

            if "agent_design_document" in shared:
                designs["agent_design_document"] = shared["agent_design_document"]

            # 快速设计文档字段
            if "requirements" in shared:
                designs["requirements"] = shared["requirements"]

            if "documentation" in shared:
                designs["documentation"] = shared["documentation"]

            # 检查生成的文档文件信息
            if "generated_documents" in shared:
                designs["generated_documents"] = shared["generated_documents"]

            # 如果有设计文档，添加到工具执行结果中
            if designs:
                tool_execution_results_updates["designs"] = designs

            result = AgentResult.create_success(
                new_messages=new_messages,
                tool_execution_results_updates=tool_execution_results_updates,
                metadata=shared.get("flow_metadata", {}),
                execution_time=execution_time
            )

            return result

        except Exception as e:
            return AgentResult.create_error(
                error=f"Failed to create agent result: {str(e)}",
                execution_time=execution_time
            )
    
    @staticmethod
    def _parse_new_messages(message_data_list: List[Any]) -> List[Message]:
        """解析新增的消息数据（支持OpenAI API标准格式）"""
        new_messages = []

        for msg_data in message_data_list:
            try:
                # 支持Message对象和字典格式
                if isinstance(msg_data, Message):
                    new_messages.append(msg_data)
                elif isinstance(msg_data, dict):
                    message = Message(
                        role=MessageRole(msg_data["role"]),
                        content=msg_data["content"],
                        timestamp=msg_data["timestamp"],
                        metadata=msg_data.get("metadata", {}),
                        tool_calls=msg_data.get("tool_calls"),
                        tool_call_id=msg_data.get("tool_call_id")
                    )
                    new_messages.append(message)
            except (KeyError, ValueError) as e:
                print(f"Warning: Failed to parse message: {e}")
                continue

        return new_messages
    




    @staticmethod
    def _validate_context(context: AgentContext) -> None:
        """
        验证AgentContext的完整性

        Args:
            context: 要验证的上下文

        Raises:
            ValueError: 当上下文数据无效时
        """
        if not context.session_id:
            raise ValueError("session_id不能为空")

        if not isinstance(context.dialogue_history, list):
            raise ValueError("dialogue_history必须是列表")

        # tool_execution_history验证已删除

        if not isinstance(context.tool_execution_results, dict):
            raise ValueError("tool_execution_results必须是字典")

        if not isinstance(context.session_metadata, dict):
            raise ValueError("session_metadata必须是字典")
    

    



# 便捷函数

def create_pocketflow_shared(
    user_input: str,
    context: AgentContext,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建pocketflow shared字典的便捷函数

    Args:
        user_input: 用户输入
        context: Agent上下文
        language: 语言选择，支持 'zh', 'en', 'ja', 'es', 'fr'（可选）

    Returns:
        pocketflow shared字典
    """
    return PocketFlowSharedFactory.create_shared_dict(user_input, context, language)


def create_agent_result(
    shared: Dict[str, Any],
    execution_time: Optional[float] = None
) -> AgentResult:
    """
    创建Agent结果的便捷函数

    Args:
        shared: 执行后的shared字典
        execution_time: 执行时间

    Returns:
        AgentResult对象
    """
    return PocketFlowSharedFactory.create_agent_result(shared, execution_time)
