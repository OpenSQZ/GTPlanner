"""
研究调研流程 - 完全重构版本
完全模仿官方示例的并发实现方式
"""

import asyncio
import os
from typing import Dict, List, Any
from pocketflow_tracing import trace_flow
from pocketflow import AsyncFlow, AsyncNode
from .keyword_research_flow import create_keyword_research_subflow
from agent.streaming import (
    emit_processing_status_from_prep,
    emit_error_from_prep,
    emit_processing_status,
    emit_error
)


class ConcurrentResearchNode(AsyncNode):
    """并发研究节点 - 在ResearchFlow内部处理并发"""

    def __init__(self):
        super().__init__()
        self.name = "concurrent_research"
        self._subflows_and_data = []
        self._execution_results = []

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备并发研究参数"""

        # 获取研究参数
        research_keywords = shared.get("research_keywords", [])
        focus_areas = shared.get("focus_areas", [])
        project_context = shared.get("project_context", "")

        # 创建子流程列表，但不创建单独的数据字典
        # 而是直接使用主shared字典，只是为每个关键词设置当前关键词
        subflows_and_keywords = []
        for keyword in research_keywords:
            keyword_subflow = create_keyword_research_subflow()
            subflows_and_keywords.append((keyword_subflow, keyword))

        # 存储到实例变量
        self._subflows_and_keywords = subflows_and_keywords

        return {
            "keywords": research_keywords,
            "focus_areas": focus_areas,
            "project_context": project_context,
            "total_keywords": len(research_keywords),
            "execution_start_time": asyncio.get_event_loop().time(),
            "streaming_session": shared.get("streaming_session")
        }

    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """并发执行关键词研究"""

        subflows_and_keywords = self._subflows_and_keywords
        keywords = prep_res["keywords"]

        # 发送处理状态事件
        await emit_processing_status_from_prep(
            prep_res,
            f"🚀 开始并发执行 {len(subflows_and_keywords)} 个关键词研究..."
        )

        start_time = asyncio.get_event_loop().time()

        # 为每个关键词创建独立的shared字典副本，但包含当前关键词信息
        async def run_keyword_research(subflow, keyword, shared_template):
            # 创建该关键词的shared字典副本
            keyword_shared = shared_template.copy()
            keyword_shared["current_keyword"] = keyword

            # 运行子流程
            result = await subflow.run_async(keyword_shared)

            # 返回关键词和结果
            return keyword, keyword_shared.get("research_findings", {}), result

        # 创建shared模板（包含所有公共数据）
        shared_template = {
            "focus_areas": prep_res["focus_areas"],
            "project_context": prep_res["project_context"],
            "streaming_session": prep_res.get("streaming_session")
        }

        # 🔧 关键：在节点内部并发执行所有子流程
        results = await asyncio.gather(*[
            run_keyword_research(subflow, keyword, shared_template)
            for subflow, keyword in subflows_and_keywords
        ], return_exceptions=True)

        execution_time = asyncio.get_event_loop().time() - start_time

        # 分析结果
        successful_results = []
        failed_results = []

        for result in results:
            if isinstance(result, Exception):
                # 发送错误事件
                await emit_error_from_prep(
                    prep_res,
                    f"⚠️ 关键词研究处理失败: {result}"
                )

                failed_results.append({
                    "keyword": "unknown",
                    "error": str(result)
                })
            else:
                keyword, keyword_result, _ = result  # 忽略 subflow_result

                if keyword_result:  # 如果有研究结果
                    successful_results.append({
                        "keyword": keyword,
                        "result": keyword_result
                    })
                else:
                    failed_results.append({
                        "keyword": keyword,
                        "error": "No research findings generated"
                    })

        successful_count = len(successful_results)
        failed_count = len(failed_results)

        # 存储结果到实例变量
        self._execution_results = {
            "successful_results": successful_results,
            "failed_results": failed_results
        }

        return {
            "execution_time": execution_time,
            "statistics": {
                "total": len(keywords),
                "successful": successful_count,
                "failed": failed_count
            },
            "success_rate": successful_count / len(keywords) if keywords else 0
        }

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """处理并发研究结果"""

        statistics = exec_res["statistics"]
        success_rate = exec_res["success_rate"]

        # 从实例变量获取详细结果
        execution_results = self._execution_results
        successful_results = execution_results["successful_results"]
        failed_results = execution_results["failed_results"]

        # 构建最终的研究结果
        keyword_results = []

        # 添加成功的结果
        for item in successful_results:
            keyword_results.append({
                "keyword": item["keyword"],
                "success": True,
                "result": item["result"]
            })

        # 添加失败的结果
        for item in failed_results:
            keyword_results.append({
                "keyword": item["keyword"],
                "success": False,
                "error": item["error"]
            })

        # 生成研究摘要
        summary = self._generate_summary(
            prep_res["keywords"],
            prep_res["focus_areas"],
            statistics["successful"],
            statistics["total"]
        )

        # 构建最终的research_findings
        research_findings = {
            "project_context": prep_res["project_context"],
            "research_keywords": prep_res["keywords"],
            "focus_areas": prep_res["focus_areas"],
            "total_keywords": statistics["total"],
            "successful_keywords": statistics["successful"],
            "failed_keywords": statistics["failed"],
            "keyword_results": keyword_results,
            "summary": summary,
            "execution_time": exec_res["execution_time"],
            "success_rate": success_rate
        }

        # 保存到shared状态
        shared["research_findings"] = research_findings

        return "research_complete"

    def _generate_summary(self, keywords: List[str], focus_areas: List[str], successful: int, total: int) -> str:
        """生成研究摘要"""

        if successful == 0:
            return "研究过程中未能获得有效结果。"

        summary_parts = [
            f"针对 {total} 个关键词进行了技术调研",
            f"成功处理了 {successful} 个关键词",
            f"主要关注点包括: {', '.join(focus_areas)}"
        ]

        return "。".join(summary_parts) + "。"


@trace_flow(flow_name="ResearchFlow")
class TracedResearchFlow(AsyncFlow):
    """带tracing的研究调研流程"""

    def __init__(self):
        super().__init__()
        # 设置并发研究节点作为起始节点
        self.start_node = ConcurrentResearchNode()

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程级准备"""
        shared["flow_start_time"] = asyncio.get_event_loop().time()

        return {
            "flow_start_time": shared["flow_start_time"],
            "operation": "research_flow"
        }

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """流程级后处理"""
        flow_duration = asyncio.get_event_loop().time() - prep_res["flow_start_time"]

        # 发送完成状态事件
        await emit_processing_status(
            shared,
            f"✅ 研究调研流程完成，耗时: {flow_duration:.2f}秒"
        )

        return exec_res


class ResearchFlow:
    """研究调研流程 - 使用带tracing的流程和并发节点"""

    def __init__(self):
        self.flow = TracedResearchFlow()

    async def run_async(self, shared: Dict[str, Any]) -> bool:
        """
        异步运行研究调研流程

        Args:
            shared: 共享状态字典，包含research_keywords, focus_areas, project_context

        Returns:
            bool: 执行是否成功
        """
        try:
            # 验证参数
            research_keywords = shared.get("research_keywords", [])
            focus_areas = shared.get("focus_areas", [])
            project_context = shared.get("project_context", "")

            if not research_keywords:
                # 发送错误事件
                await emit_error(shared, "❌ 缺少研究关键词")
                shared["research_error"] = "缺少研究关键词"
                return False

            if not focus_areas:
                # 发送错误事件
                await emit_error(shared, "❌ 缺少关注点")
                shared["research_error"] = "缺少关注点"
                return False


            # 🔧 使用带tracing的流程执行
            result = await self.flow.run_async(shared)

            if result and shared.get("research_findings"):
                # 发送成功完成事件
                await emit_processing_status(
                    shared,
                    f"✅ 研究调研流程完成，处理了 {len(research_keywords)} 个关键词"
                )
                return True
            else:
                # 发送失败事件
                await emit_error(shared, "❌ 研究调研流程未能产生有效结果")
                return False

        except Exception as e:
            # 发送异常事件
            await emit_error(shared, f"❌ 研究调研流程失败: {e}")
            shared["research_error"] = str(e)
            return False


def create_research_flow():
    """创建研究调研流程实例"""
    return ResearchFlow()
