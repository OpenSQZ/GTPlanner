"""
Node Design Dispatcher Node

批处理分发器节点，负责将Node设计任务分发给多个并行的NodeDesignNode实例。
在Flow层面实现批处理，而不是在单个Node内部循环处理。
"""

import time
from typing import Dict, Any, List
from pocketflow import AsyncNode
from agent.streaming import (
    emit_processing_status,
    emit_error
)


class NodeDesignDispatcherNode(AsyncNode):
    """Node设计分发器节点 - 为每个Node创建并行设计任务"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignDispatcherNode"
        self.description = "分发Node设计任务到并行处理节点"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集需要设计的Node列表和相关数据"""
        try:
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")
            flow_markdown = shared.get("flow_markdown", "")
            data_structure_json = shared.get("data_structure_json", "")

            # 检查必需的输入
            if not nodes_markdown:
                return {"error": "缺少Node识别结果"}

            # 从markdown中解析Node信息
            parsed_nodes = self._parse_nodes_from_markdown(nodes_markdown)

            if not parsed_nodes:
                return {"error": "无法从markdown中解析出Node信息"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "flow_markdown": flow_markdown,
                "data_structure_json": data_structure_json,
                "parsed_nodes": parsed_nodes,
                "total_nodes": len(parsed_nodes),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node design dispatch preparation failed: {str(e)}"}

    def _parse_nodes_from_markdown(self, nodes_markdown: str) -> List[Dict[str, Any]]:
        """从markdown中解析Node信息"""
        import re

        nodes = []

        # 使用正则表达式匹配三级标题（### 数字. Node名称）
        node_pattern = r'### (\d+)\.\s+(.+?)(?=\n\n|\n###|\Z)'
        matches = re.findall(node_pattern, nodes_markdown, re.DOTALL)

        for match in matches:
            node_number, node_content = match

            # 直接保存完整内容
            nodes.append(node_content.strip())

        return nodes

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：准备批处理任务数据"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            parsed_nodes = prep_result["parsed_nodes"]
            analysis_markdown = prep_result["analysis_markdown"]
            nodes_markdown = prep_result["nodes_markdown"]
            flow_markdown = prep_result["flow_markdown"]
            data_structure_json = prep_result["data_structure_json"]

            # 为每个Node准备设计任务数据
            design_tasks = []
            for i, node_content in enumerate(parsed_nodes):
                task = {
                    "task_id": f"node_design_{i}",
                    "node_content": node_content,
                    "context_data": {
                        "analysis_markdown": analysis_markdown,
                        "nodes_markdown": nodes_markdown,
                        "flow_markdown": flow_markdown,
                        "data_structure_json": data_structure_json,
                        "all_nodes": parsed_nodes
                    }
                }
                design_tasks.append(task)

            return {
                "design_tasks": design_tasks,
                "total_tasks": len(design_tasks),
                "dispatch_success": True
            }
            
        except Exception as e:
            return {"error": f"Node design dispatch failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将任务数据保存到shared，供后续批处理使用"""
        try:
            if "error" in exec_res:
                shared["node_design_dispatch_error"] = exec_res["error"]
                print(f"❌ Node设计任务分发失败: {exec_res['error']}")
                return "error"
            
            # 保存设计任务到shared
            design_tasks = exec_res["design_tasks"]
            shared["node_design_tasks"] = design_tasks
            shared["node_design_batch_size"] = len(design_tasks)
            
            # 初始化批处理结果容器
            shared["node_design_results"] = {}
            shared["node_design_completed_count"] = 0
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design_dispatch",
                "status": "completed",
                "message": f"Node设计任务分发完成：{len(design_tasks)}个任务"
            })
            
            print(f"✅ Node设计任务分发完成")
            print(f"   分发任务数: {len(design_tasks)}")
            for i, task in enumerate(design_tasks, 1):
                print(f"   - 任务{i}: {task['task_id']}")
            
            return "dispatch_complete"
            
        except Exception as e:
            shared["node_design_dispatch_post_error"] = str(e)
            print(f"❌ Node设计任务分发后处理失败: {str(e)}")
            return "error"


class NodeDesignAggregatorNode(AsyncNode):
    """Node设计聚合器节点 - 收集并整合所有Node设计结果"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignAggregatorNode"
        self.description = "聚合所有Node设计结果"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：检查批处理任务状态"""
        try:
            # 检查是否有设计任务
            design_tasks = shared.get("node_design_tasks", [])
            if not design_tasks:
                return {"error": "没有找到Node设计任务"}
            
            # 检查批处理结果
            design_results = shared.get("node_design_results", {})
            completed_count = shared.get("node_design_completed_count", 0)
            expected_count = len(design_tasks)
            
            return {
                "design_tasks": design_tasks,
                "design_results": design_results,
                "completed_count": completed_count,
                "expected_count": expected_count,
                "all_completed": completed_count >= expected_count
            }
            
        except Exception as e:
            return {"error": f"Node design aggregation preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：并发处理Node设计任务"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            design_tasks = prep_result["design_tasks"]

            # 导入NodeDesignNode用于实际设计
            from .node_design_node import NodeDesignNode
            node_design_node = NodeDesignNode()

            print(f"🔄 开始并发处理{len(design_tasks)}个Node设计任务...")

            # 使用asyncio.gather实现真正的并发处理
            import asyncio

            # 创建并发任务
            concurrent_tasks = [
                self._design_single_node_concurrent(node_design_node, task, i+1, len(design_tasks))
                for i, task in enumerate(design_tasks)
            ]

            # 并发执行所有任务
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

            # 处理结果
            design_markdowns = []
            successful_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ 任务 {i+1} 执行失败: {result}")
                elif result and result.get("success"):
                    design_markdowns.append(result["design_markdown"])
                    successful_count += 1
                else:
                    print(f"❌ 任务 {i+1} 返回无效结果")

            # 合并所有设计结果为一个markdown文档
            combined_markdown = self._combine_design_results(design_markdowns)

            print(f"✅ 并发处理完成: {successful_count}/{len(design_tasks)} 个任务成功")

            return {
                "node_design_markdown": combined_markdown,
                "aggregation_success": True,
                "processed_count": successful_count,
                "total_tasks": len(design_tasks)
            }

        except Exception as e:
            return {"error": f"Node design aggregation failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存聚合结果"""
        try:
            if "error" in exec_res:
                shared["node_design_aggregation_error"] = exec_res["error"]
                await emit_error(shared, f"❌ Node设计结果聚合失败: {exec_res['error']}")
                return "error"

            # 保存聚合的markdown结果
            node_design_markdown = exec_res["node_design_markdown"]
            shared["node_design_markdown"] = node_design_markdown

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "05_node_design.md", node_design_markdown)

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            processed_count = exec_res.get("processed_count", 0)
            total_tasks = exec_res.get("total_tasks", 0)

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design_aggregation",
                "status": "completed",
                "message": f"Node设计聚合完成：{processed_count}/{total_tasks}个任务成功"
            })

            await emit_processing_status(shared, f"✅ Node设计聚合完成")
            await emit_processing_status(shared, f"   成功处理: {processed_count}/{total_tasks} 个任务")

            return "aggregation_complete"

        except Exception as e:
            shared["node_design_aggregation_post_error"] = str(e)
            await emit_error(shared, f"❌ Node设计聚合后处理失败: {str(e)}")
            return "error"

    async def _design_single_node_concurrent(self, node_design_node, task: Dict[str, Any], task_num: int, total_tasks: int) -> Dict[str, Any]:
        """并发处理单个Node设计任务"""
        try:
            node_content = task["node_content"]
            context_data = task["context_data"]

            print(f"🔧 [{task_num}/{total_tasks}] 开始设计Node...")

            # 构建Node设计提示词
            prompt = node_design_node._build_node_design_prompt(context_data, node_content)

            # 调用LLM设计Node
            design_markdown = await node_design_node._design_single_node(prompt)

            print(f"✅ [{task_num}/{total_tasks}] Node设计完成")

            return {
                "node_content": node_content,
                "design_markdown": design_markdown,
                "success": True
            }

        except Exception as e:
            print(f"❌ [{task_num}/{total_tasks}] Node设计失败: {e}")
            return {"success": False, "error": str(e)}

    def _combine_design_results(self, design_markdowns: list) -> str:
        """合并多个Node设计结果为一个markdown文档"""
        if not design_markdowns:
            return "# Node设计结果\n\n暂无设计结果。"

        combined = "# Node设计结果\n\n"
        combined += f"共设计了 {len(design_markdowns)} 个Node。\n\n"

        for i, markdown in enumerate(design_markdowns, 1):
            combined += f"## 设计结果 {i}\n\n"
            combined += markdown + "\n\n"
            combined += "---\n\n"

        return combined.strip()

