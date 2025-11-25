"""
调用预制件函数节点 (NodeCallPrefabFunction)

直接调用预制件函数并获取实际执行结果。

功能描述：
- 使用 agent-builder-gateway-sdk 调用预制件函数
- 支持使用 API Key 进行认证
- 验证预制件的实际效果
- 将不确定的推荐过程固定为经过验证的实现方案
- 支持用户授权机制（需要文件时等待用                          户上传）

使用场景：
- 在推荐预制件后，调用此工具验证预制件的实际效果
- 确认预制件是否真正符合用户需求
- 通过实际调用，固定实现方案

授权机制：
- 如果预制件需要文件但未提供，返回待授权状态（user_decision: null）
- 前端显示文件上传界面，等待用户上传文件并授权
- 用户授权后，前端调用后端 API 重新执行（带文件参数）
"""

from typing import Dict, Any, Optional
from pocketflow import AsyncNode
import os
import uuid
import time

from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_tool_start,
    emit_tool_progress,
    emit_tool_end
)


class NodeCallPrefabFunction(AsyncNode):
    """调用预制件函数节点"""

    def __init__(self, max_retries: int = 2, wait: float = 0.5):
        """
        初始化调用预制件函数节点

        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        self.name = "NodeCallPrefabFunction"

    def _truncate_large_content(
        self,
        result: Any,
        prefab_id: str,
        function_name: str,
        max_length: int = 2000
    ) -> Any:
        """
        智能截断大内容，避免污染上下文

        策略：
        1. 检测 content 字段（文件解析结果）
        2. 如果超过 max_length，截断并添加摘要
        3. 保留其他字段不变

        Args:
            result: 预制件函数返回值（可能为 None、dict、str 等）
            prefab_id: 预制件 ID
            function_name: 函数名称
            max_length: 最大保留长度（字符数）

        Returns:
            截断后的结果
        """
        # 如果结果为 None 或不是字典，直接返回
        if result is None or not isinstance(result, dict):
            return result

        # 复制结果，避免修改原始数据
        truncated = result.copy()

        # 检查是否有 content 字段（文件解析结果）
        content = result.get("content")
        if not content or not isinstance(content, str):
            return truncated

        content_length = len(content)

        # 如果内容不大，直接返回
        if content_length <= max_length:
            return truncated

        # 截断内容
        truncated_content = content[:max_length]

        # 添加截断标记和摘要
        truncated["content"] = truncated_content
        truncated["_truncated"] = True
        truncated["_original_length"] = content_length
        truncated["_truncated_at"] = max_length
        truncated["_summary"] = f"文件内容过大（{content_length} 字符），已截断为前 {max_length} 字符。完整内容已保存，如需查看请使用输出文件。"

        print(f"⚠️  [TRUNCATE] {prefab_id}.{function_name} 内容过大: {content_length} → {max_length} 字符")

        return truncated

    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：验证参数

        Args:
            shared: pocketflow 字典共享变量

        Returns:
            准备结果字典
        """
        # 生成工具调用 ID
        call_id = str(uuid.uuid4())

        # 保存 call_id 到 shared（供后续使用）
        if "tool_call_ids" not in shared:
            shared["tool_call_ids"] = {}
        shared["tool_call_ids"]["call_prefab_function"] = call_id

        try:
            # 获取必需参数
            prefab_id = shared.get("prefab_id")
            version = shared.get("version")
            function_name = shared.get("function_name")
            parameters = shared.get("parameters", {})
            files = shared.get("files")

            # 🆕 1️⃣ 发送工具开始事件（这会更新前端的 toolCall.status = "starting"）
            await emit_tool_start(
                shared,
                tool_name="call_prefab_function",
                message=f"准备调用预制件: {prefab_id}@{version}.{function_name}",
                arguments={
                    "prefab_id": prefab_id,
                    "version": version,
                    "function_name": function_name,
                    "parameters": parameters,
                    "has_files": bool(files)
                },
                call_id=call_id
            )

            # 🔑 授权检测：如果没有 files，检查用户消息中是否包含 S3 URLs
            if not files:
                # 从 shared 中获取用户消息（最新的用户输入）
                user_message = shared.get("user_message", "")

                # 检测消息中是否包含 S3 URLs
                # 格式：s3://bucket/path/to/file.ext
                import re
                s3_pattern = r's3://[^\s]+'
                s3_urls = re.findall(s3_pattern, user_message)

                if s3_urls:
                    # 用户已提供文件，使用这些 S3 URLs
                    files = {"input": s3_urls}

                    await emit_processing_status(
                        shared,
                        f"✅ 检测到用户提供的文件（{len(s3_urls)} 个），使用这些文件执行预制件"
                    )

            # 发送 SSE 事件：开始验证参数
            await emit_processing_status(
                shared,
                f"🔧 准备调用预制件函数: {prefab_id}@{version}.{function_name}"
            )

            # 参数验证
            if not prefab_id:
                await emit_processing_status(shared, "❌ 参数错误：缺少 prefab_id")
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=False,
                    message="参数验证失败",
                    error_message="prefab_id is required",
                    call_id=call_id
                )
                return {
                    "error": "prefab_id is required",
                    "success": False
                }

            if not version:
                await emit_processing_status(shared, "❌ 参数错误：缺少 version")
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=False,
                    message="参数验证失败",
                    error_message="version is required",
                    call_id=call_id
                )
                return {
                    "error": "version is required",
                    "success": False
                }

            if not function_name:
                await emit_processing_status(shared, "❌ 参数错误：缺少 function_name")
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=False,
                    message="参数验证失败",
                    error_message="function_name is required",
                    call_id=call_id
                )
                return {
                    "error": "function_name is required",
                    "success": False
                }

            # 检查 API Key
            api_key = os.getenv("AGENT_BUILDER_API_KEY")
            if not api_key:
                await emit_processing_status(
                    shared,
                    "❌ AGENT_BUILDER_API_KEY 未配置\n"
                    "📝 请访问 https://the-agent-builder.com/workspace/api/keys 获取 API Key"
                )
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=False,
                    message="API Key 未配置",
                    error_message="AGENT_BUILDER_API_KEY environment variable not configured",
                    call_id=call_id
                )
                return {
                    "error": "AGENT_BUILDER_API_KEY environment variable not configured. Please set it to use this tool.",
                    "success": False,
                    "hint": "export AGENT_BUILDER_API_KEY='sk-your-api-key'"
                }

            await emit_processing_status(shared, "✅ 参数验证通过")

            return {
                "prefab_id": prefab_id,
                "version": version,
                "function_name": function_name,
                "parameters": parameters,
                "files": files,
                "api_key": api_key,
                "call_id": call_id,  # 🆕 传递 call_id 给 exec_async
                "_shared": shared,  # 传递 shared 给 exec_async
                "success": True
            }

        except Exception as e:
            # 🆕 发送工具失败事件
            await emit_tool_end(
                shared,
                tool_name="call_prefab_function",
                success=False,
                message="准备阶段异常",
                error_message=str(e),
                call_id=call_id
            )
            return {
                "error": f"Preparation failed: {str(e)}",
                "success": False
            }

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：调用预制件函数

        Args:
            prep_result: 准备阶段返回的结果

        Returns:
            执行结果字典
        """
        if not prep_result.get("success"):
            return prep_result

        # 从 prep_result 中获取 shared 和 call_id
        shared = prep_result.get("_shared")
        call_id = prep_result.get("call_id")

        # 记录开始时间
        start_time = time.time()

        try:
            # 动态导入 SDK（避免依赖问题）
            try:
                from gateway_sdk import GatewayClient
            except ImportError:
                if shared:
                    await emit_processing_status(
                        shared,
                        "❌ agent-builder-gateway-sdk 未安装\n"
                        "💡 请运行: pip install agent-builder-gateway-sdk>=0.7.1"
                    )
                    # 🆕 发送工具失败事件
                    await emit_tool_end(
                        shared,
                        tool_name="call_prefab_function",
                        success=False,
                        message="SDK 未安装",
                        error_message="agent-builder-gateway-sdk not installed",
                        execution_time=time.time() - start_time,
                        call_id=call_id
                    )
                return {
                    "success": False,
                    "error": "agent-builder-gateway-sdk not installed. Please run: pip install agent-builder-gateway-sdk>=0.7.1"
                }

            # 提取参数
            prefab_id = prep_result["prefab_id"]
            version = prep_result["version"]
            function_name = prep_result["function_name"]
            parameters = prep_result["parameters"]
            files = prep_result.get("files")
            api_key = prep_result["api_key"]

            # 🆕 2️⃣ 发送工具进度事件（状态变为 "running"）
            if shared:
                await emit_tool_progress(
                    shared,
                    tool_name="call_prefab_function",
                    message=f"正在调用预制件: {prefab_id}@{version}.{function_name}"
                )

            # 发送 SSE 事件：开始调用
            if shared:
                status_msg = f"🚀 正在调用预制件函数: {prefab_id}@{version}.{function_name}"
                if files:
                    file_count = sum(len(urls) if isinstance(urls, list) else 1 for urls in files.values()) if isinstance(files, dict) else len(files)
                    status_msg += f" (包含 {file_count} 个文件)"
                await emit_processing_status(shared, status_msg)

            # 🔑 使用 SDK 调用预制件
            from gateway_sdk import GatewayClient

  

            print(f"🔍 [DEBUG] 使用 SDK 调用预制件")
            print(f"🔍 [DEBUG] Prefab: {prefab_id}@{version}")
            print(f"🔍 [DEBUG] Function: {function_name}")
            print(f"🔍 [DEBUG] Parameters: {parameters}")
            print(f"🔍 [DEBUG] Files: {files}")

            # 创建 SDK 客户端
            client = GatewayClient.from_api_key(
                api_key=api_key,
                timeout=1200
            )

            # 调用预制件
            result = client.run(
                prefab_id=prefab_id,
                version=version,
                function_name=function_name,
                parameters=parameters,
                files=files
            )



            # 检查调用是否成功
            if result.status != "SUCCESS":
                error_msg = str(getattr(result, 'error', 'Unknown error'))
                execution_time = time.time() - start_time

                if shared:
                    await emit_processing_status(
                        shared,
                        f"❌ 预制件调用失败: {error_msg}"
                    )
                    # 🆕 3️⃣ 发送工具失败事件
                    await emit_tool_end(
                        shared,
                        tool_name="call_prefab_function",
                        success=False,
                        message="预制件调用失败",
                        error_message=error_msg,
                        execution_time=execution_time,
                        call_id=call_id
                    )

                return {
                    "success": False,
                    "error": f"Prefab call failed: {error_msg}",
                    "prefab_id": prefab_id,
                    "version": version,
                    "function_name": function_name
                }

            # 解析嵌套的输出结构
            # result.output 格式: {"status": "SUCCESS", "output": {...}, "files": {...}}
            call_output = result.output or {}
            
            function_result = call_output.get("output") if isinstance(call_output, dict) else None

            output_files = call_output.get("files", {}) if isinstance(call_output, dict) else {}
            job_id = result.job_id  # 任务 ID

            # 🔑 智能截断大内容，避免污染上下文
            # 只有当 function_result 不为 None 时才截断
            if function_result is not None:
                truncated_result = self._truncate_large_content(function_result, prefab_id, function_name)
            else:
                truncated_result = None

            # 计算执行时间
            execution_time = time.time() - start_time

            # 🆕 3️⃣ 发送工具成功事件
            if shared:
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=True,
                    message=f"预制件调用成功: {prefab_id}@{version}.{function_name}",
                    execution_time=execution_time,
                    result={
                        "prefab_id": prefab_id,
                        "version": version,
                        "function_name": function_name,
                        "job_id": job_id,
                        "has_output_files": bool(output_files),
                        "output_file_count": sum(len(urls) for urls in output_files.values()) if output_files else 0
                    },
                    call_id=call_id
                )

            # 发送 SSE 事件：调用成功（详细消息）
            if shared:
                success_msg = f"✅ 预制件调用成功！\n"
                success_msg += f"📦 预制件: {prefab_id}@{version}\n"
                success_msg += f"🔧 函数: {function_name}\n"
                success_msg += f"🆔 任务ID: {job_id}\n"
                success_msg += f"⏱️  执行时间: {execution_time:.2f}s"

                if output_files:
                    file_count = sum(len(urls) for urls in output_files.values())
                    success_msg += f"\n📁 输出文件: {file_count} 个"

                # 如果内容被截断，提示用户
                if truncated_result and isinstance(truncated_result, dict) and truncated_result.get("_truncated"):
                    success_msg += f"\n⚠️  内容过大已截断（原始长度: {truncated_result.get('_original_length')} 字符）"

                await emit_processing_status(shared, success_msg)

            # 返回结果
            return {
                "success": True,
                "prefab_id": prefab_id,
                "version": version,
                "function_name": function_name,
                "function_result": truncated_result,  # 截断后的函数返回值
                "output_files": output_files,         # 输出文件（如果有）
                "job_id": job_id,                     # 任务 ID
                "execution_time": execution_time,     # 🆕 添加执行时间
                "user_decision": "executed",          # 🔑 已执行状态
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            execution_time = time.time() - start_time

            # 🆕 发送工具失败事件
            if shared:
                await emit_tool_end(
                    shared,
                    tool_name="call_prefab_function",
                    success=False,
                    message="执行阶段异常",
                    error_message=str(e),
                    execution_time=execution_time,
                    call_id=call_id
                )

            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "prefab_id": prep_result.get("prefab_id"),
                "version": prep_result.get("version"),
                "function_name": prep_result.get("function_name")
            }

    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_result: Dict[str, Any],
        exec_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        后处理阶段：将结果保存到 shared

        Args:
            shared: pocketflow 字典共享变量
            prep_result: 准备阶段返回的结果
            exec_result: 执行阶段返回的结果

        Returns:
            None（成功）或错误消息
        """
        try:
            # 将结果保存到 shared（供后续使用）
            if exec_result.get("success"):
                # 保存调用历史（可选）
                if "prefab_call_history" not in shared:
                    shared["prefab_call_history"] = []

                shared["prefab_call_history"].append({
                    "prefab_id": exec_result["prefab_id"],
                    "version": exec_result["version"],
                    "function_name": exec_result["function_name"],
                    "function_result": exec_result["function_result"],
                    "output_files": exec_result.get("output_files"),
                    "job_id": exec_result.get("job_id")
                })

                # 保存最新的调用结果
                shared["last_prefab_call_result"] = exec_result

                # 发送 SSE 事件：保存成功
                await emit_processing_status(
                    shared,
                    "💾 调用结果已保存到历史记录"
                )

            return None  # 成功

        except Exception as e:
            await emit_processing_status(
                shared,
                f"⚠️ 保存结果时出错: {str(e)}"
            )
            return f"Post-processing failed: {str(e)}"
