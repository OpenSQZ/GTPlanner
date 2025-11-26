"""
工具执行器

负责Function Calling工具的执行和结果处理，支持并行执行和流式反馈。
"""

import json
import time
import asyncio
from typing import Dict, List, Any
from gtplanner.agent.function_calling import execute_agent_tool, validate_tool_arguments
from gtplanner.agent.streaming.stream_types import StreamEventBuilder, ToolCallStatus
from gtplanner.agent.streaming.stream_interface import StreamingSession


class ToolExecutor:
    """现代化工具执行器"""

    def __init__(self):
        # 移除复杂的统计功能，专注核心执行
        pass
    
    async def execute_tools_parallel(
        self,
        tool_calls: List[Dict[str, Any]],  # OpenAI标准格式的工具调用
        shared: Dict[str, Any],
        streaming_session: StreamingSession
    ) -> List[Dict[str, Any]]:
        """
        并行执行多个工具调用

        Args:
            tool_calls: 工具调用列表
            shared: 共享状态字典
            streaming_session: 流式会话（必填）

        Returns:
            工具执行结果列表
        """
        if not tool_calls:
            return []

        # 🐛 调试日志：记录接收到的工具调用
        print(f"🔧 ToolExecutor 接收到 {len(tool_calls)} 个工具调用")
        for i, tc in enumerate(tool_calls):
            print(f"  [{i}] {tc['function']['name']} - call_id: {tc['id']}")

        # TODO: 考虑是否需要强制顺序执行以避免并发调用问题
        # 当前代码使用 asyncio.gather 并行执行所有工具，但某些工具之间存在依赖关系
        # 如果 LLM 违反了提示词约束并发调用多个工具，可能导致数据不一致
        # 解决方案：检测到多个工具调用时，改为顺序执行或报错

        # 创建异步任务
        tasks = []
        for tool_call in tool_calls:
            # 使用OpenAI标准格式
            tool_name = tool_call["function"]["name"]
            call_id = tool_call["id"]

            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError as e:
                # 记录JSON解析错误
                error_msg = f"JSON解析失败: {str(e)}, 原始参数: {tool_call['function']['arguments']}"
                self._record_error(shared, "ToolExecutor.json_parse", error_msg, tool_name)
                continue

            # 验证工具参数
            validation = validate_tool_arguments(tool_name, arguments)
            if not validation["valid"]:
                # 记录验证错误
                self._record_error(shared, "ToolExecutor.validation",
                                 f"参数验证失败: {validation['errors']}", tool_name)
                continue

            # 创建异步任务
            task = self._execute_single_tool(
                call_id, tool_name, arguments, shared, streaming_session
            )
            tasks.append(task)

        # 等待所有工具执行完成
        if tasks:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._process_tool_results(tool_results, shared)

        return []
    
    async def _execute_single_tool(
        self,
        call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        shared: Dict[str, Any],
        streaming_session: StreamingSession
    ) -> Dict[str, Any]:
        """
        执行单个工具调用

        Args:
            call_id: 调用ID
            tool_name: 工具名称
            arguments: 工具参数
            shared: 共享状态字典
            streaming_session: 流式会话（必填）

        Returns:
            工具执行结果
        """
        try:
            # 流式响应：发送工具开始执行事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="starting",
                call_id=call_id,  # 使用LLM生成的工具调用ID
                progress_message=f"正在调用{tool_name}工具...",
                arguments=arguments
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_start(streaming_session.session_id, tool_status)
            )

            # 立即发送进度事件，将状态更新为 running
            tool_status_running = ToolCallStatus(
                tool_name=tool_name,
                status="running",
                call_id=call_id,
                progress_message=f"正在执行{tool_name}工具..."
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_progress(streaming_session.session_id, tool_status_running)
            )

            start_time = time.time()
            tool_result = await execute_agent_tool(tool_name, arguments, shared)
            execution_time = time.time() - start_time

            # 流式响应：发送工具完成事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="completed" if tool_result.get("success", False) else "failed",
                call_id=call_id,  # 使用LLM生成的工具调用ID
                progress_message=f"{tool_name}工具执行完成" if tool_result.get("success", False) else f"{tool_name}工具执行失败",
                result=tool_result,
                execution_time=execution_time,
                error_message=tool_result.get("error") if not tool_result.get("success", False) else None
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_end(streaming_session.session_id, tool_status)
            )

            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": tool_result,
                "call_id": call_id,
                "success": tool_result.get("success", False),
                "execution_time": execution_time
            }

        except Exception as e:
            # 记录详细错误信息到shared字典
            error_msg = f"工具执行异常: {str(e)}, 工具: {tool_name}, 参数: {arguments}"
            self._record_error(shared, "ToolExecutor.execute", error_msg, tool_name)

            # 流式响应：发送工具错误事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="failed",
                call_id=call_id,  # 使用LLM生成的工具调用ID
                progress_message=f"{tool_name}工具执行异常",
                result={"success": False, "error": str(e)},
                execution_time=0.0,
                error_message=str(e)
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_end(streaming_session.session_id, tool_status)
            )

            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": {"success": False, "error": str(e)},
                "call_id": call_id,
                "success": False,
                "execution_time": 0.0
            }

    def _record_error(self, shared: Dict[str, Any], source: str, error: str, tool_name: str = ""):
        """记录错误到shared字典"""
        if "errors" not in shared:
            shared["errors"] = []

        error_info = {
            "source": source,
            "error": error,
            "tool_name": tool_name,
            "timestamp": time.time()
        }
        shared["errors"].append(error_info)
    
    def _process_tool_results(self, tool_results: List[Any], shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理工具执行结果，过滤异常

        Args:
            tool_results: 原始工具结果列表
            shared: 共享状态字典

        Returns:
            处理后的工具结果列表
        """
        processed_results = []
        for result in tool_results:
            if isinstance(result, Exception):
                # 记录异常到shared，不打印到控制台
                self._record_error(shared, "ToolExecutor.process_results", str(result))
                processed_results.append({
                    "tool_name": "unknown",
                    "arguments": {},
                    "result": {"success": False, "error": str(result)},
                    "call_id": "error",
                    "success": False,
                    "execution_time": 0.0
                })
            else:
                processed_results.append(result)

        return processed_results
    