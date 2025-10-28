"""
工具执行器

负责Function Calling工具的执行和结果处理，支持并行执行和流式反馈。
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Set
from agent.function_calling import execute_agent_tool, validate_tool_arguments
from agent.streaming.stream_types import StreamEventBuilder, ToolCallStatus
from agent.streaming.stream_interface import StreamingSession

class AsyncToolExecutionPool:
    """异步工具执行池管理器
    
    提供工具调用的并发控制、超时管理和资源限制功能，避免系统资源耗尽。
    """
    
    def __init__(self, max_concurrent_tools: int = 5, default_timeout: float = 60.0):
        """
        初始化异步工具执行池
        
        Args:
            max_concurrent_tools: 最大并发工具调用数
            default_timeout: 默认工具执行超时时间（秒）
        """
        self.max_concurrent_tools = max_concurrent_tools
        self.default_timeout = default_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent_tools)
        self.active_calls: Set[str] = set()  # 跟踪活跃的调用ID
        
    async def execute_with_limits(
        self,
        call_id: str,
        execute_func,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        在限制条件下执行工具调用
        
        Args:
            call_id: 调用ID
            execute_func: 要执行的异步函数
            *args: 传递给函数的位置参数
            timeout: 超时时间（秒），默认使用池的默认超时
            **kwargs: 传递给函数的关键字参数
            
        Returns:
            工具执行结果
        """
        # 确保调用ID唯一
        if call_id in self.active_calls:
            call_id = f"{call_id}_{int(time.time())}_{hash(str(args)) % 1000}"
        
        self.active_calls.add(call_id)
        timeout = timeout or self.default_timeout
        
        try:
            # 使用信号量限制并发
            async with self.semaphore:
                # 设置超时
                try:
                    # 执行工具调用
                    result = await asyncio.wait_for(
                        execute_func(*args, **kwargs),
                        timeout=timeout
                    )
                    return result
                except asyncio.TimeoutError:
                    return {
                        "tool_name": args[0] if args else "unknown",
                        "arguments": args[1] if len(args) > 1 else {},
                        "result": {"success": False, "error": f"工具执行超时（{timeout}秒）"},
                        "call_id": call_id,
                        "success": False,
                        "execution_time": timeout
                    }
        finally:
            # 确保无论如何都从活跃调用中移除
            if call_id in self.active_calls:
                self.active_calls.remove(call_id)

class ToolExecutor:
    """现代化工具执行器"""

    def __init__(self):
        # 移除复杂的统计功能，专注核心执行
        # pass

        # 初始化异步工具执行池
        self.execution_pool = AsyncToolExecutionPool(
            max_concurrent_tools=5,  # 控制最大并发工具调用数
            default_timeout=60.0     # 设置默认超时时间
        )
        # 添加工具优先级映射，频繁使用的工具获得更高优先级
        self.tool_priority = {
            "research": 1,
            "short_planning": 1,
            "tool_recommend": 2
        }        
    
    async def execute_tools_parallel(
        self,
        tool_calls: List[Dict[str, Any]],  # OpenAI标准格式的工具调用
        shared: Dict[str, Any],
        streaming_session: StreamingSession
    ) -> List[Dict[str, Any]]:
        """
        并行执行多个工具调用（支持优先级排序和并发控制）

        Args:
            tool_calls: 工具调用列表
            shared: 共享状态字典
            streaming_session: 流式会话（必填）

        Returns:
            工具执行结果列表
        """
        if not tool_calls:
            return []

        # 创建异步任务
        # tasks = []
        # 预处理和参数验证，同时创建任务配置
        task_configs = []        
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
            # task = self._execute_single_tool(
            #     call_id, tool_name, arguments, shared, streaming_session
            # )
            
            # 获取工具优先级，未配置的工具默认为较低优先级
            priority = self.tool_priority.get(tool_name, 3)
            
            # 添加到任务配置列表，包含优先级信息
            task_configs.append({
                "tool_call": tool_call,
                "tool_name": tool_name,
                "call_id": call_id,
                "arguments": arguments,
                "priority": priority
            })
        
        # 根据优先级排序任务，优先级数字越小越优先执行
        task_configs.sort(key=lambda x: x["priority"])
        
        # 创建异步任务列表
        tasks = []
        for config in task_configs:
            # 根据工具类型设置不同的超时时间
            timeout = 90.0 if config["tool_name"] == "research" else 60.0
            
            # 创建带限制的执行任务
            task = self.execution_pool.execute_with_limits(
                call_id=config["call_id"],
                execute_func=self._execute_single_tool,
                call_id_inner=config["call_id"],
                tool_name=config["tool_name"],
                arguments=config["arguments"],
                shared=shared,
                streaming_session=streaming_session,
                timeout=timeout
            )            
            tasks.append(task)

        # 等待所有任务完成，过滤None结果（来自参数验证失败）
        results = []
        if tasks:
        #     tool_results = await asyncio.gather(*tasks, return_exceptions=True)
        #     return self._process_tool_results(tool_results, shared)

        # return []
            tool_results = await asyncio.gather(*tasks, return_exceptions=False)
            results = [r for r in tool_results if r is not None]
        
        return results        
    
    async def _execute_single_tool(
        self,
        call_id_inner: str,
        tool_name: str,
        arguments: Dict[str, Any],
        shared: Dict[str, Any],
        streaming_session: StreamingSession
    ) -> Dict[str, Any]:
        """
        执行单个工具调用（通过异步池调用）

        Args:
            call_id_inner: 调用ID
            tool_name: 工具名称
            arguments: 工具参数
            shared: 共享状态字典
            streaming_session: 流式会话（必填）

        Returns:
            工具执行结果
        """
        # try:
        # 使用一个轻量级的函数进行实际执行，避免捕获超时异常
        async def _execute_actual():        
            # 流式响应：发送工具开始执行事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="starting",
                call_id=call_id_inner,  # 使用LLM生成的工具调用ID
                progress_message=f"正在调用{tool_name}工具...",
                arguments=arguments
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_start(streaming_session.session_id, tool_status)
            )

            # 发送进度事件，将状态更新为 running
            tool_status_running = ToolCallStatus(
                tool_name=tool_name,
                status="running",
                call_id=call_id_inner,
                progress_message=f"正在执行{tool_name}工具..."
            )
            await streaming_session.emit_event(
                StreamEventBuilder.tool_call_progress(streaming_session.session_id, tool_status_running)
            )

            # 执行工具调用（注意：超时由外部的execute_with_limits处理）
            start_time = time.time()
            tool_result = await execute_agent_tool(tool_name, arguments, shared)
            execution_time = time.time() - start_time

            # 流式响应：发送工具完成事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="completed" if tool_result.get("success", False) else "failed",
                call_id=call_id_inner,  # 使用LLM生成的工具调用ID
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
                "call_id": call_id_inner,
                "success": tool_result.get("success", False),
                "execution_time": execution_time
            }

        
        
        try:
            return await _execute_actual()
        except Exception as e:
            # 记录详细错误信息到shared字典
            error_msg = f"工具执行异常: {str(e)}, 工具: {tool_name}, 参数: {arguments}"
            self._record_error(shared, "ToolExecutor.execute", error_msg, tool_name)

            # 流式响应：发送工具错误事件
            tool_status = ToolCallStatus(
                tool_name=tool_name,
                status="failed",
                call_id=call_id_inner,  # 使用LLM生成的工具调用ID
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
                "call_id": call_id_inner,
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
    