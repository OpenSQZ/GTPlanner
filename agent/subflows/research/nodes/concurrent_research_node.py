"""
并发研究节点 - 参考官方示例实现真正的并发处理

在单个节点内部处理多个关键词的并发研究，而不是并发多个Flow
"""

import asyncio
from typing import Dict, List, Any
from pocketflow import AsyncNode
from ..flows.keyword_research_flow import create_keyword_research_subflow
from agent.streaming import (
    emit_processing_status_from_prep,
    emit_error_from_prep,
    emit_processing_status,
    emit_error
)


class ConcurrentResearchNode(AsyncNode):
    """
    并发研究节点 - 参考官方示例的实现方式
    
    在单个节点内部并发处理多个关键词，保持trace的正确时间线
    """

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
        
        # 验证参数
        if not research_keywords:
            return {"error": "缺少研究关键词"}
        
        if not focus_areas:
            return {"error": "缺少关注点"}
        
        
        # 创建子流程和数据对
        subflows_and_data = []
        for keyword in research_keywords:
            # 创建关键词研究子流程
            keyword_subflow = create_keyword_research_subflow()
            
            # 准备关键词数据
            keyword_data = {
                "current_keyword": keyword,
                "focus_areas": focus_areas,
                "project_context": project_context
            }
            
            subflows_and_data.append((keyword_subflow, keyword_data))
        
        # 存储到实例变量，避免序列化问题
        self._subflows_and_data = subflows_and_data
        
        # 返回可序列化的数据用于tracing
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
        
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        subflows_and_data = self._subflows_and_data
        keywords = prep_res["keywords"]

        # 发送处理状态事件
        await emit_processing_status_from_prep(
            prep_res,
            f"🚀 开始并发执行 {len(subflows_and_data)} 个关键词研究..."
        )

        start_time = asyncio.get_event_loop().time()
        
        # 🔧 关键：在单个节点内部并发执行所有子流程
        results = await asyncio.gather(*[
            subflow.run_async(data)
            for subflow, data in subflows_and_data
        ], return_exceptions=True)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # 分析结果
        successful_results = []
        failed_results = []
        
        for i, (result, (subflow, data)) in enumerate(zip(results, subflows_and_data)):
            keyword = data["current_keyword"]
            
            if isinstance(result, Exception):
                # 发送错误事件
                await emit_error_from_prep(
                    prep_res,
                    f"⚠️ 关键词 '{keyword}' 处理失败: {result}"
                )

                failed_results.append({
                    "keyword": keyword,
                    "error": str(result)
                })
            else:
                # 从子流程的shared字典中获取结果
                keyword_result = data.get("keyword_report", {})
                successful_results.append({
                    "keyword": keyword,
                    "result": keyword_result
                })
        
        successful_count = len(successful_results)
        failed_count = len(failed_results)
        
        
        # 存储结果到实例变量
        self._execution_results = {
            "successful_results": successful_results,
            "failed_results": failed_results
        }
        
        # 返回可序列化的执行结果
        return {
            "execution_time": execution_time,
            "statistics": {
                "total": len(keywords),
                "successful": successful_count,
                "failed": failed_count
            },
            "keywords_processed": keywords,
            "success_rate": successful_count / len(keywords) if keywords else 0
        }

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """处理并发研究结果"""
        
        statistics = exec_res["statistics"]
        execution_time = exec_res["execution_time"]
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
            "execution_time": execution_time,
            "success_rate": success_rate
        }
        
        # 保存到shared状态
        shared["research_findings"] = research_findings
        shared["concurrent_statistics"] = statistics
        shared["concurrent_execution_time"] = execution_time
        
        # 确定成功状态
        if success_rate >= 0.8:  # 80%成功率
            shared["research_status"] = "success"
            # 发送成功事件
            await emit_processing_status(
                shared,
                f"🎉 并发研究成功: {success_rate:.1%} 成功率"
            )
            return "research_complete"
        elif success_rate >= 0.5:  # 50%成功率
            shared["research_status"] = "partial_success"
            # 发送部分成功事件
            await emit_processing_status(
                shared,
                f"⚠️ 并发研究部分成功: {success_rate:.1%} 成功率"
            )
            return "research_partial"
        else:
            shared["research_status"] = "failed"
            # 发送失败事件
            await emit_error(
                shared,
                f"❌ 并发研究失败: {success_rate:.1%} 成功率"
            )
            return "research_failed"

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
