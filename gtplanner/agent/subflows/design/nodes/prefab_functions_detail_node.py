"""
Prefab Functions Detail Node - 预制件函数详情查询后置节点

设计流程结束后，查询所有推荐预制件的函数详情，并转换为文档格式，便于下游使用。
"""

import time
import json
import httpx
from typing import Dict, Any, List
from pocketflow import AsyncNode

from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error,
    emit_design_document
)


class PrefabFunctionsDetailNode(AsyncNode):
    """预制件函数详情查询节点 - 批量查询推荐预制件的函数详情并生成文档"""

    def __init__(self):
        super().__init__()
        self.name = "PrefabFunctionsDetailNode"
        self.description = "批量查询推荐预制件的函数详情并生成文档"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集推荐的预制件信息"""
        try:
            await emit_processing_status(shared, "📋 准备查询预制件函数详情...")

            # 获取推荐的预制件列表
            recommended_prefabs = shared.get("recommended_prefabs", [])

            if not recommended_prefabs:
                return {
                    "skip": True,
                    "message": "没有推荐的预制件，跳过函数详情查询"
                }

            # 提取需要查询的预制件信息（id, version, functions）
            prefabs_to_query = []
            for prefab in recommended_prefabs:
                if isinstance(prefab, dict) and "id" in prefab:
                    prefab_id = prefab.get("id")
                    version = prefab.get("version", "latest")
                    functions = prefab.get("functions", [])

                    # 只查询有函数列表的预制件
                    if functions:
                        prefabs_to_query.append({
                            "id": prefab_id,
                            "version": version,
                            "name": prefab.get("name", ""),
                            "description": prefab.get("description", ""),
                            "functions": [f.get("name") for f in functions if isinstance(f, dict) and "name" in f]
                        })

            if not prefabs_to_query:
                return {
                    "skip": True,
                    "message": "推荐的预制件中没有函数信息，跳过查询"
                }

            await emit_processing_status(
                shared,
                f"📦 找到 {len(prefabs_to_query)} 个预制件需要查询详情"
            )

            return {
                "skip": False,
                "prefabs_to_query": prefabs_to_query,
                "timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"Prefab functions detail preparation failed: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：批量查询预制件函数详情"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            if prep_result.get("skip"):
                return {
                    "skip": True,
                    "message": prep_result.get("message", "Skipped")
                }

            prefabs_to_query = prep_result["prefabs_to_query"]

            # 从配置获取 prefab-gateway 地址
            from gtplanner.utils.config_manager import get_prefab_gateway_url
            gateway_url = get_prefab_gateway_url()

            if not gateway_url:
                raise ValueError("Prefab gateway URL not configured")

            # 批量查询函数详情
            prefabs_details = []

            async with httpx.AsyncClient(timeout=30.0) as client:
                for prefab_info in prefabs_to_query:
                    prefab_id = prefab_info["id"]
                    version = prefab_info["version"]
                    function_names = prefab_info["functions"]

                    # 查询该预制件的所有函数详情
                    functions_details = []
                    for func_name in function_names:
                        try:
                            url = f"{gateway_url}/v1/public/prefabs/{prefab_id}/functions/{func_name}"
                            params = {}
                            if version and version != "latest":
                                params["version"] = version

                            response = await client.get(url, params=params)
                            response.raise_for_status()
                            function_detail = response.json()

                            functions_details.append({
                                "name": func_name,
                                "detail": function_detail
                            })

                        except Exception as e:
                            # 单个函数查询失败不影响整体流程
                            functions_details.append({
                                "name": func_name,
                                "error": str(e)
                            })

                    # 保存该预制件的详情
                    prefabs_details.append({
                        "id": prefab_id,
                        "version": version,
                        "name": prefab_info["name"],
                        "description": prefab_info["description"],
                        "functions": functions_details
                    })

            return {
                "skip": False,
                "prefabs_details": prefabs_details,
                "query_time": time.time()
            }

        except Exception as e:
            return {"error": f"Prefab functions detail query failed: {str(e)}"}

    async def post_async(self, shared: Dict[str, Any], prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理阶段：生成函数详情文档并发送事件"""
        try:
            if "error" in exec_result:
                error_msg = exec_result["error"]
                shared["prefab_functions_detail_error"] = error_msg
                await emit_error(shared, f"❌ 预制件函数详情查询失败: {error_msg}")
                print(f"❌ 预制件函数详情查询失败: {error_msg}")
                return "error"

            if exec_result.get("skip"):
                skip_msg = exec_result.get("message", "Skipped")
                await emit_processing_status(shared, f"⏭️  {skip_msg}")
                print(f"⏭️  {skip_msg}")
                return "default"

            # 生成函数详情文档
            await emit_processing_status(shared, "📝 正在生成预制件函数详情文档...")

            prefabs_details = exec_result["prefabs_details"]
            document_content = self._format_functions_document(prefabs_details)

            # 保存到 shared（供下游节点使用）
            shared["prefab_functions_details"] = prefabs_details
            shared["prefab_functions_document"] = document_content

            # 发送文档事件到前端
            await emit_design_document(shared, "prefabs_info.md", document_content)

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "prefab_functions_detail",
                "status": "completed",
                "message": f"已查询 {len(prefabs_details)} 个预制件的函数详情"
            })

            await emit_processing_status(
                shared,
                f"✅ 已生成预制件函数详情文档（{len(prefabs_details)} 个预制件）"
            )
            print(f"✅ 预制件函数详情查询完成，共 {len(prefabs_details)} 个预制件")

            return "default"

        except Exception as e:
            error_msg = str(e)
            shared["prefab_functions_detail_post_error"] = error_msg
            await emit_error(shared, f"❌ 预制件函数详情文档生成失败: {error_msg}")
            print(f"❌ 预制件函数详情文档生成失败: {error_msg}")
            return "error"

    def _format_functions_document(self, prefabs_details: List[Dict[str, Any]]) -> str:
        """格式化预制件函数详情为 Markdown 文档"""
        lines = [
            "# 预制件函数详情",
            "",
            "本文档包含所有推荐预制件的函数详细信息，包括参数、返回值、使用示例等。",
            "",
            "---",
            ""
        ]

        for prefab in prefabs_details:
            prefab_id = prefab["id"]
            version = prefab["version"]
            name = prefab["name"]
            description = prefab["description"]
            functions = prefab["functions"]

            # 预制件标题
            lines.append(f"## {name}")
            lines.append("")
            lines.append(f"**ID**: `{prefab_id}`")
            lines.append(f"**版本**: `{version}`")
            lines.append(f"**描述**: {description}")
            lines.append("")

            # 函数列表
            if functions:
                lines.append("### 函数列表")
                lines.append("")

                for func in functions:
                    func_name = func["name"]

                    if "error" in func:
                        # 查询失败的函数
                        lines.append(f"#### `{func_name}`")
                        lines.append("")
                        lines.append(f"⚠️ **查询失败**: {func['error']}")
                        lines.append("")
                    else:
                        # 成功查询的函数
                        detail = func["detail"]
                        lines.append(f"#### `{func_name}`")
                        lines.append("")

                        # 函数描述
                        if detail.get("description"):
                            lines.append(f"**描述**: {detail['description']}")
                            lines.append("")

                        # 参数定义
                        if detail.get("parameters"):
                            lines.append("**参数**:")
                            lines.append("")
                            lines.append("```json")
                            lines.append(json.dumps(detail["parameters"], indent=2, ensure_ascii=False))
                            lines.append("```")
                            lines.append("")

                        # 返回值定义
                        if detail.get("returns"):
                            lines.append("**返回值**:")
                            lines.append("")
                            lines.append("```json")
                            lines.append(json.dumps(detail["returns"], indent=2, ensure_ascii=False))
                            lines.append("```")
                            lines.append("")

                        # 使用示例
                        if detail.get("examples"):
                            lines.append("**使用示例**:")
                            lines.append("")
                            for example in detail["examples"]:
                                if isinstance(example, dict):
                                    if example.get("description"):
                                        lines.append(f"- {example['description']}")
                                    if example.get("code"):
                                        lines.append("  ```")
                                        lines.append(f"  {example['code']}")
                                        lines.append("  ```")
                                elif isinstance(example, str):
                                    lines.append(f"- {example}")
                            lines.append("")

                        # 其他元数据
                        if detail.get("metadata"):
                            lines.append("**元数据**:")
                            lines.append("")
                            lines.append("```json")
                            lines.append(json.dumps(detail["metadata"], indent=2, ensure_ascii=False))
                            lines.append("```")
                            lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)
