"""
ReAct Orchestrator Node

基于Function Calling的ReAct主控制器节点，采用模块化设计。
负责处理单次ReAct推理和决策逻辑。
"""

## ✅ 已实现：处理content中包含标签的方式 - 使用ContentToolCallAdapter适配器
from typing import Dict, List, Any, Optional
from pocketflow import AsyncNode

# 导入OpenAI SDK和Function Calling工具
from utils.openai_client import get_openai_client
from agent.function_calling import get_agent_function_definitions

# 导入流式响应类型
from agent.streaming.stream_types import StreamCallbackType
from agent.streaming.stream_interface import StreamingSession

# 导入重构后的组件
from .constants import (
    ErrorMessages,
    DefaultValues
)

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes

from .tool_executor import ToolExecutor




class ReActOrchestratorNode(AsyncNode):
    """ReAct主控制器节点 - 模块化设计"""

    def __init__(self):
        super().__init__()
        self.name = "ReActOrchestratorNode"
        self.description = "基于Function Calling的模块化ReAct主控制器节点"

        # 初始化OpenAI客户端
        self.openai_client = get_openai_client()

        # 获取可用的Function Calling工具
        self.available_tools = get_agent_function_definitions()

        # 初始化组件
        self.tool_executor = ToolExecutor()

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """异步准备ReAct执行环境（无状态版本）"""
        try:
            return {
                "success": True,
                "shared_data": shared
            }

        except Exception as e:
            return {"error": f"{ErrorMessages.REACT_PREP_FAILED}: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步ReAct推理和决策逻辑 - 基于Function Calling（支持流式响应）"""

        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            shared_data = prep_result.get("shared_data", {})

            # 直接使用dialogue_history中的messages（完整或压缩过的聊天记录）
            dialogue_history = shared_data.get("dialogue_history", {})
            messages = dialogue_history.get("messages", [])

            # 使用Function Calling执行（传递shared_data作为shared参数）
            result = await self._execute_with_function_calling(messages, shared_data)

            return result

        except Exception as e:
            # 在没有shared字典访问权限时，只能返回错误
            return {
                "error": f"{ErrorMessages.REACT_EXEC_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False,
                "exec_error": str(e)  # 添加详细错误信息供post_async处理
            }

    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """异步更新共享状态（无状态版本）"""
        try:
            if "error" in exec_res:
                # 记录exec阶段的错误到shared
                if "errors" not in shared:
                    shared["errors"] = []
                shared["errors"].append({
                    "source": "ReActOrchestratorNode.exec",
                    "error": exec_res.get("exec_error", exec_res["error"]),
                    "timestamp": __import__('time').time()
                })
                shared["react_error"] = exec_res["error"]
                return "error"

            # 更新ReAct循环计数
            self._increment_react_cycle(shared)

            # 获取执行结果
            tool_calls = exec_res.get("tool_calls", [])

            # 注意：assistant消息已经在_unified_function_calling_cycle中被添加到shared["new_messages"]
            # 这里不需要再次添加，避免重复保存

            # 处理工具调用结果（提取到shared字典的工具执行结果字段）
            if tool_calls:
                self._process_tool_calls(shared, tool_calls)

            # 简化路由：总是等待用户，让LLM在回复中自然引导下一步
            return "wait_for_user"

        except Exception as e:
            # 记录错误到shared字典，不打印到控制台
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": "ReActOrchestratorNode.post",
                "error": str(e),
                "timestamp": __import__('time').time()
            })
            shared["react_post_error"] = str(e)
            return "error"



    def _add_assistant_message(self, shared: Dict[str, Any], message: str, tool_calls: Optional[List[Dict[str, Any]]]) -> None:
        """添加助手消息到预留字段（OpenAI API标准格式）"""
        from agent.context_types import create_assistant_message

        assistant_message = create_assistant_message(
            content=message,
            tool_calls=tool_calls or None
        )

        # 添加到预留字段
        if "new_messages" not in shared:
            shared["new_messages"] = []

        shared["new_messages"].append(assistant_message)

    def _add_tool_message(self, shared: Dict[str, Any], tool_call_id: str, content: str) -> None:
        """添加tool消息到预留字段（OpenAI API标准格式）"""
        from agent.context_types import create_tool_message

        tool_message = create_tool_message(
            content=content,
            tool_call_id=tool_call_id
        )

        # 添加到预留字段
        if "new_messages" not in shared:
            shared["new_messages"] = []

        shared["new_messages"].append(tool_message)

    def _process_tool_calls(self, shared: Dict[str, Any], tool_calls: List[Dict[str, Any]]) -> None:
        """处理工具调用结果（提取到shared字典）"""
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            tool_result = tool_call.get("result")

            if tool_name and tool_result:
                # 提取工具执行结果到主shared字典
                self._extract_tool_execution_results(shared, tool_name, tool_result)

    def _extract_tool_execution_results(self, shared: Dict[str, Any], tool_name: str, tool_result: Dict[str, Any]) -> None:
        """提取工具执行结果到主shared字典"""
        # 根据工具名称提取特定的结果
        if tool_name == "tool_recommend" and tool_result.get("success"):
            result_data = tool_result.get("result", {})
            recommended_tools = result_data.get("recommended_tools")
            if recommended_tools:
                shared["recommended_tools"] = recommended_tools

        elif tool_name == "research" and tool_result.get("success"):
            result_data = tool_result.get("result", {})
            # research工具的result直接就是research_findings内容
            if result_data:
                shared["research_findings"] = result_data

        elif tool_name == "short_planning" and tool_result.get("success"):
            result_data = tool_result.get("result", {})
            # short_planning工具的result直接就是规划内容
            if result_data:
                shared["short_planning"] = result_data

    def _increment_react_cycle(self, shared: Dict[str, Any]) -> int:
        """增加ReAct循环计数"""
        current_count = shared.get("react_cycle_count", 0)
        new_count = current_count + 1
        shared["react_cycle_count"] = new_count
        return new_count

    async def _execute_with_function_calling(
        self,
        messages: List[Dict[str, str]],
        shared: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用Function Calling执行ReAct逻辑（统一递归架构）"""
        try:
            # 获取流式响应参数
            streaming_session = shared.get("streaming_session")
            streaming_callbacks = shared.get("streaming_callbacks", {})

            # 如果有流式会话，使用统一的递归函数
            if streaming_session and streaming_callbacks:
                return await self._unified_function_calling_cycle(
                    messages, shared, streaming_session, streaming_callbacks, recursion_depth=0
                )
            else:
                # 非流式处理暂不支持，返回提示信息
                return {
                    "user_message": "当前仅支持流式处理模式，请确保提供了正确的流式会话参数。",
                    "tool_calls": [],
                    "reasoning": "非流式处理模式未实现",
                    "confidence": 0.0,
                    "decision_success": False,
                    "execution_mode": "non_streaming_not_supported"
                }

        except Exception as e:
            return {
                "user_message": "",
                "tool_calls": [],
                "reasoning": f"执行失败: {str(e)}",
                "confidence": 0.0,
                "decision_success": False,
                "execution_mode": "error"
            }



    async def _unified_function_calling_cycle(
        self,
        messages: List[Dict[str, Any]],
        shared: Dict[str, Any],
        streaming_session: StreamingSession,
        streaming_callbacks: Dict[str, Any],
        recursion_depth: int = 0,
        max_recursion_depth: int = 5
    ) -> Dict[str, Any]:
        """
        统一的Function Calling递归循环处理器

        这个函数合并了原来的_execute_with_streaming和_process_function_calling_cycle的功能，
        消除了代码重复，提供了一个统一的递归处理流程。

        Args:
            messages: 消息历史
            shared: 共享状态字典
            streaming_session: 流式会话
            streaming_callbacks: 流式回调
            recursion_depth: 当前递归深度
            max_recursion_depth: 最大递归深度限制

        Returns:
            最终的执行结果
        """
        # 防止无限递归
        if recursion_depth >= max_recursion_depth:
            return {
                "user_message": f"已达到最大递归深度({max_recursion_depth})，停止进一步的工具调用。",
                "tool_calls": [],
                "reasoning": f"递归深度限制，停止在第{recursion_depth}轮",
                "confidence": 0.7,
                "decision_success": True,
                "execution_mode": "recursion_limit_reached"
            }

        try:
            # 步骤1: 调用LLM并处理流式响应
            assistant_message_content, assistant_tool_calls = await self._call_llm_with_streaming(
                messages, shared, streaming_session, streaming_callbacks
            )

            # 步骤2: 现在工具调用转换在源头进行，直接使用结果
            # assistant_message_content 已经是过滤后的显示内容
            # assistant_tool_calls 已经包含了从content标签转换的工具调用

            # 步骤3: 保存assistant消息到shared字典（使用清理后的内容）
            self._add_assistant_message(shared, assistant_message_content, assistant_tool_calls)

            # 步骤4: 处理工具调用或返回最终结果
            if assistant_tool_calls:
                # 将assistant消息添加到历史（使用清理后的内容）
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_message_content,
                    "tool_calls": assistant_tool_calls
                }
                messages.append(assistant_message)

                # 步骤5: 执行工具调用
                tool_execution_results = await self._execute_tools_with_callbacks(
                    assistant_tool_calls, shared, streaming_session, streaming_callbacks
                )

                # 步骤6: 将工具结果添加到消息历史
                self._add_tool_results_to_messages(
                    messages, assistant_tool_calls, tool_execution_results, shared
                )

                # 步骤6: 递归调用处理后续响应
                return await self._unified_function_calling_cycle(
                    messages, shared, streaming_session, streaming_callbacks,
                    recursion_depth + 1, max_recursion_depth
                )
            else:
                # 没有工具调用，发送 assistant_message_end 事件然后返回最终结果
                if StreamCallbackType.ON_LLM_END in streaming_callbacks:
                    await streaming_callbacks[StreamCallbackType.ON_LLM_END](
                        streaming_session,
                        complete_message=assistant_message_content,
                        tool_calls=[]  # 没有工具调用，传递空列表
                    )

                return {
                    "user_message": assistant_message_content,
                    "tool_calls": [],
                    "reasoning": f"完成{recursion_depth + 1}轮Function Calling循环" if recursion_depth > 0 else "LLM直接回复，无需工具调用",
                    "confidence": 0.9,
                    "decision_success": True,
                    "execution_mode": f"complete_depth_{recursion_depth + 1}" if recursion_depth > 0 else "direct_response"
                }

        except Exception as e:
            # 在递归执行中记录错误到shared
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": f"ReActOrchestratorNode.unified_cycle_depth_{recursion_depth}",
                "error": str(e),
                "timestamp": __import__('time').time()
            })
            return {
                "user_message": f"在第{recursion_depth + 1}轮Function Calling中出现错误：{str(e)}",
                "tool_calls": [],
                "reasoning": f"第{recursion_depth + 1}轮执行失败",
                "confidence": 0.0,
                "decision_success": False,
                "execution_mode": "recursion_error"
            }

    async def _call_llm_with_streaming(
        self,
        messages: List[Dict[str, Any]],
        shared: Dict[str, Any],
        streaming_session: StreamingSession,
        streaming_callbacks: Dict[str, Any]
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        调用LLM并处理流式响应

        Returns:
            (assistant_message_content, assistant_tool_calls)
        """
        try:
            # 触发LLM开始回调
            if StreamCallbackType.ON_LLM_START in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_START](streaming_session)

            # 获取语言设置和系统提示词
            language = shared.get("language")  # 从shared字典获取语言选择
            system_prompt = get_prompt(
                PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
                language=language
            )

            # 使用流式API（启用工具调用标签过滤）
            stream = self.openai_client.chat_completion_stream(
                system_prompt=system_prompt,
                messages=messages,
                tools=self.available_tools,
                parallel_tool_calls=True,
                filter_tool_tags=True
            )

            # 收集流式响应
            assistant_message_content = ""
            current_tool_calls = {}
            chunk_index = 0

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 处理内容片段（现在已经在源头过滤了工具调用标签）
                    if delta.content:
                        assistant_message_content += delta.content

                        # 直接输出已过滤的内容
                        if StreamCallbackType.ON_LLM_CHUNK in streaming_callbacks:
                            await streaming_callbacks[StreamCallbackType.ON_LLM_CHUNK](
                                streaming_session,
                                chunk_content=delta.content,
                                chunk_index=chunk_index
                            )
                            chunk_index += 1

                    # 处理工具调用
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            index = tool_call_delta.index
                            if index not in current_tool_calls:
                                current_tool_calls[index] = {
                                    "id": tool_call_delta.id or "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tool_call_delta.id:
                                current_tool_calls[index]["id"] = tool_call_delta.id
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_calls[index]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    current_tool_calls[index]["function"]["arguments"] += tool_call_delta.function.arguments

            # 构建工具调用列表
            assistant_tool_calls = [tool_call for tool_call in current_tool_calls.values() if tool_call["id"]]

            # 触发LLM结束回调（使用已过滤的内容，并传递 tool_calls 信息）
            if StreamCallbackType.ON_LLM_END in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_END](
                    streaming_session,
                    complete_message=assistant_message_content,
                    tool_calls=assistant_tool_calls  # 传递工具调用信息
                )

            return assistant_message_content, assistant_tool_calls

        except Exception as e:
            # LLM调用失败，记录错误并抛出异常让上层处理
            print(f"❌ LLM调用失败: {str(e)}")
            raise Exception(f"LLM调用失败: {str(e)}")



    async def _execute_tools_with_callbacks(
        self,
        tool_calls: List[Dict[str, Any]],
        shared: Dict[str, Any],
        streaming_session: StreamingSession,
        streaming_callbacks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """执行工具调用并处理回调"""
        # 触发工具调用开始回调
        for tool_call in tool_calls:
            if StreamCallbackType.ON_TOOL_START in streaming_callbacks:
                import json
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except:
                    arguments = tool_call["function"]["arguments"]

                await streaming_callbacks[StreamCallbackType.ON_TOOL_START](
                    streaming_session,
                    tool_name=tool_call["function"]["name"],
                    arguments=arguments,
                    call_id=tool_call["id"]  # 传递LLM生成的工具调用ID
                )

        # 执行工具调用
        tool_execution_results = await self.tool_executor.execute_tools_parallel(
            tool_calls, shared, streaming_session
        )

        # 触发工具调用结束回调
        for tool_result in tool_execution_results:
            if StreamCallbackType.ON_TOOL_END in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_TOOL_END](
                    streaming_session,
                    tool_name=tool_result.get("tool_name", "unknown"),
                    result=tool_result.get("result", {}),
                    execution_time=tool_result.get("execution_time", 0),
                    success=tool_result.get("success", True),
                    error_message=tool_result.get("error")
                )

        return tool_execution_results

    def _add_tool_results_to_messages(
        self,
        messages: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        tool_execution_results: List[Dict[str, Any]],
        shared: Dict[str, Any]
    ) -> None:
        """将工具执行结果添加到消息历史和shared字典"""
        import json

        # 提取工具执行结果到shared字典
        for tool_result in tool_execution_results:
            tool_name = tool_result.get("tool_name")
            if tool_name and tool_result.get("success"):
                actual_tool_result = tool_result.get("result", {})
                self._extract_tool_execution_results(shared, tool_name, actual_tool_result)

        # 将工具结果添加到消息历史
        for i, tool_result in enumerate(tool_execution_results):
            tool_call_id = tool_calls[i]["id"]
            result_content = json.dumps(tool_result.get("result", {}), ensure_ascii=False)

            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result_content
            }
            messages.append(tool_message)

            # 保存tool消息到shared字典
            self._add_tool_message(shared, tool_call_id, result_content)



